"""
cloud_orchestrator.py — Platinum Cloud Agent Orchestrator
Runs 24/7 on Oracle Cloud VM, managed by PM2.

Responsibilities:
  - Start 4 watchers as daemon threads: Gmail, Twitter, LinkedIn, Facebook
  - Watchdog: auto-restart any watcher that crashes
  - Folder watcher: trigger Claude when new .md files appear in Needs_Action/
  - Scheduled Claude cycle: every 2 hours (catchup) and on any new work detected
  - Git sync: pull before each Claude run, push after
  - Write heartbeat to Updates/ every 5 minutes

PM2 commands:
  pm2 start cloud_orchestrator.py --interpreter python3 --name cloud-agent
  pm2 save && pm2 startup

Modes:
  python3 cloud_orchestrator.py           daemon (recommended)
  python3 cloud_orchestrator.py --now     daemon + run one Claude cycle immediately
  python3 cloud_orchestrator.py --cron    one-shot cycle then exit
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import schedule
from dotenv import load_dotenv

VAULT = Path(__file__).parent.resolve()
load_dotenv(VAULT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [cloud-orchestrator] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("cloud_orchestrator")

# ── Prompts ───────────────────────────────────────────────────────────────────

CLOUD_PROMPT = """Read CLOUD_CLAUDE.md then execute the Cloud Daily Workflow:

1. Check Needs_Action/email/ for unclaimed .md files
2. Claim each by moving it to In_Progress/cloud_agent/
3. Triage using SKILL_Gmail_Triage — write draft replies to Pending_Approval/email/
4. Check Needs_Action/social/ for unclaimed .md files
5. Claim each by moving it to In_Progress/cloud_agent/
6. Triage using SKILL_Twitter_Draft, SKILL_LinkedIn_Draft, SKILL_Facebook_Instagram
   — write social drafts to Pending_Approval/social/
7. Write Updates/cloud_status.md with today's counts
8. Log all actions to Logs/YYYY-MM-DD.json using SKILL_Audit_Logger
9. Output: TASK_COMPLETE when both Needs_Action/email/ and Needs_Action/social/ are empty"""

CLAUDE_TIMEOUT    = int(os.getenv("CLAUDE_TIMEOUT", "600"))     # 10 min
WATCHDOG_INTERVAL = int(os.getenv("WATCHDOG_INTERVAL", "30"))   # 30 sec
FOLDER_POLL       = 60   # seconds between Needs_Action/ checks
MIN_CYCLE_GAP     = 120  # seconds minimum between Claude runs (debounce)

_last_claude_run: float = 0.0
_claude_lock = threading.Lock()

# ── Git sync ──────────────────────────────────────────────────────────────────

def _git(cmd: list, timeout: int = 60) -> bool:
    try:
        r = subprocess.run(cmd, cwd=str(VAULT.parent), capture_output=True,
                           text=True, timeout=timeout)
        if r.returncode != 0:
            log.warning("git %s: %s", cmd[1], r.stderr.strip()[:120])
        return r.returncode == 0
    except Exception as e:
        log.warning("git error: %s", e)
        return False


def git_pull() -> None:
    log.info("git pull --rebase --autostash")
    _git(["git", "pull", "--rebase", "--autostash"])


def git_push(msg: str) -> None:
    _git(["git", "add", str(VAULT)])
    status = subprocess.run(
        ["git", "status", "--porcelain", str(VAULT)],
        cwd=str(VAULT.parent), capture_output=True, text=True, timeout=10
    )
    if not status.stdout.strip():
        return
    _git(["git", "commit", "-m", f"[cloud] {msg}"])
    _git(["git", "push"], timeout=90)
    log.info("git push: %s", msg)

# ── Heartbeat ─────────────────────────────────────────────────────────────────

def write_heartbeat() -> None:
    hb = VAULT / "Updates" / "heartbeat.md"
    hb.parent.mkdir(parents=True, exist_ok=True)
    hb.write_text(
        f"cloud_agent_heartbeat: {datetime.now(timezone.utc).isoformat()}\n",
        encoding="utf-8",
    )

# ── Work detection ────────────────────────────────────────────────────────────

def has_pending_work() -> bool:
    """True if any unprocessed .md files in Needs_Action/email/ or /social/."""
    in_progress = VAULT / "In_Progress" / "cloud_agent"
    for domain in ("email", "social"):
        folder = VAULT / "Needs_Action" / domain
        if folder.exists():
            # Files not already claimed (not in In_Progress)
            claimed = {f.name for f in in_progress.glob("*.md")} if in_progress.exists() else set()
            for f in folder.glob("*.md"):
                if f.name not in claimed:
                    return True
    return False

# ── Claude runner ─────────────────────────────────────────────────────────────

def run_claude() -> None:
    global _last_claude_run
    with _claude_lock:
        now = time.time()
        if now - _last_claude_run < MIN_CYCLE_GAP:
            log.info("Skipping Claude run — too soon since last run (debounce)")
            return
        _last_claude_run = now

    git_pull()

    if not has_pending_work():
        log.info("No pending work — skipping Claude cycle")
        write_heartbeat()
        return

    log.info("Starting Cloud Claude reasoning cycle…")
    claude_bin = shutil.which("claude") or "claude"
    cmd = [claude_bin, "--dangerously-skip-permissions", "--print", CLOUD_PROMPT]

    try:
        result = subprocess.run(
            cmd, cwd=str(VAULT), timeout=CLAUDE_TIMEOUT, check=False
        )
        log.info("Claude cycle finished (exit %d)", result.returncode)
    except FileNotFoundError:
        log.error("'claude' not found — install: npm install -g @anthropic/claude-code")
        return
    except subprocess.TimeoutExpired:
        log.error("Claude cycle timed out after %ds", CLAUDE_TIMEOUT)
        return

    git_push("triage cycle complete")
    write_heartbeat()

# ── Folder watcher thread ─────────────────────────────────────────────────────

def watch_needs_action() -> None:
    """Poll Needs_Action every 60s — trigger Claude immediately on new files."""
    log.info("Folder watcher started (polling every %ds)", FOLDER_POLL)
    while True:
        time.sleep(FOLDER_POLL)
        try:
            if has_pending_work():
                log.info("New work detected in Needs_Action/ — triggering Claude")
                threading.Thread(target=run_claude, name="ClaudeRun", daemon=True).start()
        except Exception as e:
            log.error("Folder watcher error: %s", e)

# ── Watcher registry ──────────────────────────────────────────────────────────

def _watcher_registry(vault: Path) -> list:
    iv = lambda k, d: int(os.getenv(k, d))
    hl = os.getenv("HEADLESS", "true").lower() != "false"

    def gmail():
        sys.path.insert(0, str(vault))
        from gmail_watcher import GmailWatcher
        GmailWatcher(
            vault_path=str(vault),
            check_interval=iv("GMAIL_INTERVAL", "120"),
            needs_action_subdir="email",
        ).run()

    def twitter():
        sys.path.insert(0, str(vault))
        from twitter_watcher import TwitterWatcher
        TwitterWatcher(
            vault_path=str(vault),
            check_interval=iv("TWITTER_INTERVAL", "300"),
            needs_action_subdir="social",
        ).run()

    def linkedin():
        sys.path.insert(0, str(vault))
        from linkedin_watcher import LinkedInWatcher
        LinkedInWatcher(
            vault_path=str(vault),
            check_interval=iv("LINKEDIN_INTERVAL", "300"),
            headless=hl,
            needs_action_subdir="social",
        ).run()

    def facebook():
        sys.path.insert(0, str(vault))
        from facebook_watcher import FacebookWatcher
        FacebookWatcher(
            vault_path=str(vault),
            check_interval=iv("FACEBOOK_INTERVAL", "600"),
            needs_action_subdir="social",
        ).run()

    return [
        ("Gmail",
         lambda: (vault / "credentials.json").exists(),
         gmail),
        ("Twitter",
         lambda: bool(os.getenv("TWITTER_BEARER_TOKEN")),
         twitter),
        ("LinkedIn",
         lambda: bool(os.getenv("LINKEDIN_EMAIL")) and bool(os.getenv("LINKEDIN_PASSWORD")),
         linkedin),
        ("Facebook",
         lambda: bool(os.getenv("FACEBOOK_ACCESS_TOKEN")) and bool(os.getenv("FACEBOOK_PAGE_ID")),
         facebook),
    ]

# ── Watchdog supervisor ───────────────────────────────────────────────────────

def _spawn(name: str, fn) -> threading.Thread:
    def _run():
        try:
            fn()
        except Exception as exc:
            log.error("%s watcher crashed: %s", name, exc, exc_info=True)

    t = threading.Thread(target=_run, name=name, daemon=True)
    t.start()
    log.info("%s watcher started (tid=%d)", name, t.ident)
    return t


def run_watchdog(vault: Path) -> None:
    """Start all watchers whose prerequisites pass, restart any that die."""
    registry = _watcher_registry(vault)
    threads: dict[str, threading.Thread] = {}

    for name, guard, fn in registry:
        if guard():
            threads[name] = _spawn(name, fn)
        else:
            log.warning("%s watcher skipped — prerequisite missing (check .env)", name)

    while True:
        time.sleep(WATCHDOG_INTERVAL)
        for name, guard, fn in registry:
            t = threads.get(name)
            if t is not None and not t.is_alive():
                log.warning("%s watcher died — restarting", name)
                threads[name] = _spawn(name, fn)

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Platinum Cloud Agent Orchestrator")
    parser.add_argument("--vault", default=str(VAULT), help="Vault root (default: current dir)")
    parser.add_argument("--now",   action="store_true", help="Run Claude cycle immediately on start")
    parser.add_argument("--cron",  action="store_true", help="One-shot cycle then exit")
    args = parser.parse_args()

    vault = Path(args.vault).resolve()
    load_dotenv(vault / ".env")
    log.info("Platinum Cloud Orchestrator | Vault: %s | Agent: cloud_agent", vault)

    # ── One-shot mode ──────────────────────────────────────────────────────────
    if args.cron:
        log.info("Cron mode — running one cycle then exiting")
        run_claude()
        return

    # ── Daemon mode ────────────────────────────────────────────────────────────
    if args.now:
        run_claude()

    # Start watchdog (all 4 watchers)
    threading.Thread(
        target=run_watchdog, args=(vault,), name="Watchdog", daemon=True
    ).start()

    # Start folder watcher (triggers Claude on new Needs_Action files)
    threading.Thread(
        target=watch_needs_action, name="FolderWatcher", daemon=True
    ).start()

    # Scheduled: catchup cycle every 2 hours (catches anything missed by folder watcher)
    schedule.every(2).hours.do(run_claude)

    # Heartbeat every 5 min (via health_monitor.py, but also here as backup)
    schedule.every(5).minutes.do(write_heartbeat)

    log.info(
        "Scheduled: 2h catchup cycle | 5m heartbeat | "
        "4 watchers active | folder polling every %ds", FOLDER_POLL
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        log.info("Cloud Orchestrator stopped")


if __name__ == "__main__":
    main()
