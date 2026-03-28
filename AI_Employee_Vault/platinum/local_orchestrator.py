"""
local_orchestrator.py — Platinum Local Agent Orchestrator (Windows)

Runs on the user's local Windows machine.
Manages the approval workflow, triggers email-mcp, and keeps Dashboard up-to-date.

Responsibilities:
  - Auto git-pull every 5 min to get Cloud Agent's new drafts
  - Watch Approved/ every 10 seconds — email-mcp picks up approved files automatically
  - Run Local Claude cycle daily at 08:00 (or on demand)
  - Check Cloud heartbeat — alert in Dashboard if Cloud is silent > 30 min
  - Merge Updates/cloud_status.md into Dashboard.md
  - Git push after local changes

Modes:
  uv run python local_orchestrator.py          daemon
  uv run python local_orchestrator.py --now    run one Claude cycle immediately
  uv run python local_orchestrator.py --pull   just pull + check for pending approvals

To run email-mcp separately (in another terminal):
  cd platinum/mcp_servers/email-mcp && node index.js
"""

import argparse
import logging
import os
import platform
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
    format="%(asctime)s [local-orchestrator] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("local_orchestrator")

# ── Config ────────────────────────────────────────────────────────────────────

CLAUDE_TIMEOUT         = int(os.getenv("CLAUDE_TIMEOUT", "900"))       # 15 min
GIT_PULL_INTERVAL      = int(os.getenv("GIT_PULL_INTERVAL", "300"))    # 5 min
APPROVED_POLL_INTERVAL = 10                                             # seconds
HEARTBEAT_STALE_MIN    = int(os.getenv("HEARTBEAT_STALE_MINUTES", "30"))

LOCAL_PROMPT = """Read LOCAL_CLAUDE.md then execute the Local Agent Workflow:

1. git pull to get latest Cloud Agent changes
2. Check Updates/heartbeat.md — if last heartbeat > 30 min ago, flag in Dashboard.md
3. Read Updates/cloud_status.md — merge counts into Dashboard.md
4. Scan Pending_Approval/email/ — list items awaiting approval in Dashboard.md
5. Scan Pending_Approval/social/ — list items awaiting approval in Dashboard.md
6. Check Approved/ — note any files there for email-mcp to process
7. Process any remaining Needs_Action/email/ or Needs_Action/social/ items
   that were not claimed by Cloud Agent
8. Update Dashboard.md with current system state (you are sole Dashboard writer)
9. Log all actions to Logs/YYYY-MM-DD.json
10. Output: TASK_COMPLETE"""

# ── Git sync ──────────────────────────────────────────────────────────────────

def git_pull() -> bool:
    """Pull latest from remote. Returns True if new changes received."""
    try:
        r = subprocess.run(
            ["git", "pull", "--rebase", "--autostash"],
            cwd=str(VAULT.parent), capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0:
            log.warning("git pull stderr: %s", r.stderr.strip()[:120])
            return False
        new_changes = "Already up to date" not in r.stdout
        if new_changes:
            log.info("New changes pulled from Cloud: %s", r.stdout.strip()[:120])
        else:
            log.debug("git pull: already up to date")
        return new_changes
    except Exception as e:
        log.warning("git pull failed: %s", e)
        return False


def git_push(msg: str) -> None:
    try:
        vault_root = VAULT.parent
        subprocess.run(["git", "add", str(VAULT)], cwd=str(vault_root),
                       capture_output=True, timeout=30)
        status = subprocess.run(
            ["git", "status", "--porcelain", str(VAULT)],
            cwd=str(vault_root), capture_output=True, text=True, timeout=10
        )
        if not status.stdout.strip():
            return
        subprocess.run(["git", "commit", "-m", f"[local] {msg}"],
                       cwd=str(vault_root), capture_output=True, timeout=20)
        subprocess.run(["git", "push"], cwd=str(vault_root),
                       capture_output=True, timeout=60)
        log.info("git push: %s", msg)
    except Exception as e:
        log.warning("git push failed: %s", e)

# ── Cloud heartbeat check ─────────────────────────────────────────────────────

def check_cloud_heartbeat() -> None:
    """Check how long ago Cloud Agent last wrote a heartbeat. Log warning if stale."""
    hb_file = VAULT / "Updates" / "heartbeat.md"
    if not hb_file.exists():
        log.warning("Cloud heartbeat file missing — Cloud Agent may not have started yet")
        return
    try:
        content = hb_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            if "heartbeat:" in line:
                ts_str = line.split("heartbeat:")[1].strip()
                ts     = datetime.fromisoformat(ts_str)
                age_min = (datetime.now(timezone.utc) - ts).total_seconds() / 60
                if age_min > HEARTBEAT_STALE_MIN:
                    log.warning(
                        "ALERT: Cloud Agent heartbeat is %.0f min old (threshold: %d min). "
                        "Cloud VM may be down!", age_min, HEARTBEAT_STALE_MIN
                    )
                else:
                    log.info("Cloud heartbeat OK (%.1f min ago)", age_min)
                return
    except Exception as e:
        log.warning("Could not parse heartbeat file: %s", e)

# ── Pending approval check ────────────────────────────────────────────────────

def check_pending_approvals() -> None:
    """Log how many items are waiting for approval in each domain."""
    for domain in ("email", "social"):
        folder = VAULT / "Pending_Approval" / domain
        if folder.exists():
            count = len(list(folder.glob("*.md")))
            if count > 0:
                log.info("Pending approvals — %s: %d file(s) awaiting your review in "
                         "platinum/Pending_Approval/%s/", domain, count, domain)

# ── Claude runner ─────────────────────────────────────────────────────────────

def _find_claude() -> list[str]:
    if platform.system() == "Windows":
        for c in ("claude.cmd", "claude"):
            if shutil.which(c):
                return [c]
        return ["claude.cmd"]
    return [shutil.which("claude") or "claude"]


def run_claude() -> None:
    log.info("Pulling latest Cloud changes before Local cycle…")
    git_pull()
    check_cloud_heartbeat()
    check_pending_approvals()

    log.info("Starting Local Claude reasoning cycle…")
    cmd = _find_claude() + ["--dangerously-skip-permissions", "--print", LOCAL_PROMPT]
    try:
        result = subprocess.run(
            cmd, cwd=str(VAULT), timeout=CLAUDE_TIMEOUT, check=False,
            shell=(platform.system() == "Windows"),
        )
        log.info("Local Claude cycle finished (exit %d)", result.returncode)
    except FileNotFoundError:
        log.error("'claude' not found — install: npm install -g @anthropic/claude-code")
        return
    except subprocess.TimeoutExpired:
        log.error("Claude cycle timed out after %ds", CLAUDE_TIMEOUT)
        return

    git_push("local triage cycle complete")

# ── Auto git-pull loop ────────────────────────────────────────────────────────

def auto_pull_loop() -> None:
    """Pull every GIT_PULL_INTERVAL seconds. Alert if new pending approvals arrive."""
    log.info("Auto-pull loop started (every %ds)", GIT_PULL_INTERVAL)
    while True:
        time.sleep(GIT_PULL_INTERVAL)
        try:
            new_changes = git_pull()
            if new_changes:
                check_cloud_heartbeat()
                check_pending_approvals()
        except Exception as e:
            log.error("Auto-pull error: %s", e)

# ── Approved folder watcher ───────────────────────────────────────────────────

def watch_approved() -> None:
    """
    Poll Approved/ every 10s.
    The email-mcp Node.js process handles sending — this just logs for visibility.
    """
    approved = VAULT / "Approved"
    seen: set[str] = set()
    log.info("Watching Approved/ every %ds (email-mcp handles send)", APPROVED_POLL_INTERVAL)

    while True:
        time.sleep(APPROVED_POLL_INTERVAL)
        try:
            if not approved.exists():
                continue
            for f in approved.glob("*.md"):
                if f.name not in seen:
                    seen.add(f.name)
                    log.info(
                        "Approved file detected: %s — email-mcp will process this", f.name
                    )
        except Exception as e:
            log.error("Approved/ watcher error: %s", e)

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Platinum Local Agent Orchestrator")
    parser.add_argument("--vault",  default=str(VAULT))
    parser.add_argument("--now",    action="store_true", help="Run Claude cycle immediately")
    parser.add_argument("--pull",   action="store_true", help="Pull + check pending then exit")
    args = parser.parse_args()

    vault = Path(args.vault).resolve()
    load_dotenv(vault / ".env")
    log.info("Platinum Local Orchestrator | Vault: %s | Agent: local_agent", vault)

    # ── Pull-only mode ─────────────────────────────────────────────────────────
    if args.pull:
        git_pull()
        check_cloud_heartbeat()
        check_pending_approvals()
        return

    # ── Daemon mode ────────────────────────────────────────────────────────────
    if args.now:
        run_claude()

    # Background: Approved/ watcher
    threading.Thread(
        target=watch_approved, name="ApprovedWatcher", daemon=True
    ).start()

    # Background: auto git-pull every 5 min
    threading.Thread(
        target=auto_pull_loop, name="AutoPull", daemon=True
    ).start()

    # Scheduled: daily Claude cycle at 08:00
    schedule.every().day.at("08:00").do(run_claude)

    log.info(
        "Local orchestrator running | "
        "Daily cycle at 08:00 | "
        "Auto-pull every %ds | "
        "Watching Approved/ every %ds",
        GIT_PULL_INTERVAL, APPROVED_POLL_INTERVAL
    )
    log.info(
        "TIP: Start email-mcp in a separate terminal: "
        "cd platinum/mcp_servers/email-mcp && node index.js"
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        log.info("Local Orchestrator stopped")


if __name__ == "__main__":
    main()
