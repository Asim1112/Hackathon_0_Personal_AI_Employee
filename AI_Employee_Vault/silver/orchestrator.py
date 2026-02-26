"""
orchestrator.py — Silver AI Employee Orchestrator

Starts Gmail / LinkedIn / WhatsApp watchers as daemon threads, supervises them
with a watchdog that auto-restarts any that crash, and fires the Claude reasoning
loop at 08:00 daily via the `schedule` library.

Modes:
  python orchestrator.py           daemon: watchers + 8 AM schedule loop
  python orchestrator.py --now     daemon + immediate Claude run on startup
  python orchestrator.py --cron    one-shot: run Claude once and exit
                                   (OS cron handles the schedule — no long-running process)

Cron fallback (add to crontab / Task Scheduler instead of running daemon):
  0 8 * * 1-6  cd /path/to/silver && uv run python orchestrator.py --cron

Dependencies (all in pyproject.toml — run `uv sync` to install):
  schedule>=1.2.0, python-dotenv>=1.0.0
  Plus watcher deps: playwright>=1.49.0, google-api-python-client>=2.126.0

Run:  uv run python orchestrator.py
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
from pathlib import Path

import schedule
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

VAULT = Path(__file__).parent.resolve()
load_dotenv(VAULT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [orchestrator] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("orchestrator")

CLAUDE_PROMPT = (
    "Read CLAUDE.md then run: SKILL_Daily_Briefing → SKILL_Gmail_Triage → "
    "SKILL_WhatsApp_Triage → SKILL_LinkedIn_Draft → SKILL_Reasoning_Loop → "
    "SKILL_Process_Needs_Action → SKILL_Update_Dashboard. "
    "Write TASK_COMPLETE when Needs_Action/ is empty."
)

WATCHDOG_INTERVAL = 30   # seconds between thread health checks
CLAUDE_TIMEOUT    = 600  # 10-minute cap on each Claude cycle

# ── Watcher registry ──────────────────────────────────────────────────────────
# Each entry: (display_name, guard_fn, target_fn)
# guard_fn  → returns True when prerequisites are met (skip with warning if False)
# target_fn → blocking call that runs the watcher; orchestrator wraps it in a thread

def _watcher_registry(vault: Path) -> list:
    iv = lambda k, d: int(os.getenv(k, d))
    hl = os.getenv("HEADLESS", "true").lower() != "false"

    def gmail():
        sys.path.insert(0, str(vault))
        from gmail_watcher import GmailWatcher
        GmailWatcher(vault_path=str(vault), check_interval=iv("GMAIL_INTERVAL", "120")).run()

    def linkedin():
        sys.path.insert(0, str(vault))
        from linkedin_watcher import LinkedInWatcher
        LinkedInWatcher(vault_path=str(vault), check_interval=iv("LINKEDIN_INTERVAL", "300"),
                        headless=hl).run()

    def whatsapp():
        sys.path.insert(0, str(vault))
        from whatsapp_watcher import WhatsAppWatcher
        WhatsAppWatcher(vault_path=str(vault),
                        session_path=str(vault / "whatsapp_session"),
                        check_interval=iv("WHATSAPP_INTERVAL", "30"),
                        headless=hl).run()

    return [
        ("Gmail",
         lambda: (vault / "credentials.json").exists(),
         gmail),
        ("LinkedIn",
         lambda: bool(os.getenv("LINKEDIN_EMAIL")) and bool(os.getenv("LINKEDIN_PASSWORD")),
         linkedin),
        ("WhatsApp",
         lambda: (vault / "whatsapp_session").exists(),
         whatsapp),
    ]

# ── Claude runner ─────────────────────────────────────────────────────────────

def _find_claude() -> list[str]:
    """Locate claude CLI — on Windows npm installs a .cmd wrapper."""
    if platform.system() == "Windows":
        for candidate in ("claude.cmd", "claude"):
            if shutil.which(candidate):
                return [candidate]
        return ["claude.cmd"]
    return ["claude"]


def run_claude(vault: Path) -> None:
    log.info("Claude reasoning cycle starting…")
    cmd = _find_claude() + ["--dangerously-skip-permissions", "--print", CLAUDE_PROMPT]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(vault), timeout=CLAUDE_TIMEOUT, check=False,
            shell=(platform.system() == "Windows"),
        )
        log.info(f"Claude cycle finished (exit {result.returncode})")
    except FileNotFoundError:
        log.error("'claude' / 'claude.cmd' not found — install Claude Code and add it to PATH")
    except subprocess.TimeoutExpired:
        log.error(f"Claude cycle timed out after {CLAUDE_TIMEOUT}s")

# ── Watchdog supervisor ───────────────────────────────────────────────────────

def _spawn(name: str, fn) -> threading.Thread:
    """Wrap fn in error-catching shell, start as daemon thread."""
    def _run():
        try:
            fn()
        except Exception as exc:
            log.error(f"{name} watcher crashed: {exc}", exc_info=True)
    t = threading.Thread(target=_run, name=name, daemon=True)
    t.start()
    log.info(f"{name} watcher started (tid={t.ident})")
    return t


def run_watchdog(vault: Path) -> None:
    """
    Start all watchers whose guards pass, then loop every WATCHDOG_INTERVAL
    seconds and restart any dead threads. Runs in its own daemon thread.
    """
    registry = _watcher_registry(vault)
    threads: dict[str, threading.Thread] = {}

    for name, guard, fn in registry:
        if guard():
            threads[name] = _spawn(name, fn)
        else:
            log.warning(f"{name} watcher skipped — prerequisite missing "
                        f"(check .env / credentials / session files)")

    while True:
        time.sleep(WATCHDOG_INTERVAL)
        for name, guard, fn in registry:
            t = threads.get(name)
            if t is not None and not t.is_alive():
                log.warning(f"{name} watcher is dead — restarting…")
                threads[name] = _spawn(name, fn)

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Silver AI Employee Orchestrator")
    parser.add_argument("--vault", default=".", help="Vault root (default: current dir)")
    parser.add_argument("--now",  action="store_true", help="Run Claude cycle immediately on startup")
    parser.add_argument("--cron", action="store_true",
                        help="One-shot mode: run Claude cycle once then exit (for OS cron)")
    args = parser.parse_args()

    vault = Path(args.vault).resolve()
    log.info(f"Silver AI Employee Orchestrator | Vault: {vault}")

    # ── Cron / one-shot mode ──────────────────────────────────────────────────
    if args.cron:
        log.info("Cron mode — running one Claude cycle then exiting")
        run_claude(vault)
        return

    # ── Daemon mode ───────────────────────────────────────────────────────────
    if args.now:
        run_claude(vault)

    # Watchdog runs in background; schedule loop runs in main thread
    threading.Thread(target=run_watchdog, args=(vault,), name="Watchdog", daemon=True).start()

    schedule.every().day.at("08:00").do(run_claude, vault=vault)
    log.info("Scheduled: Claude reasoning loop daily at 08:00 | Watchdog active")

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        log.info("Orchestrator stopped (KeyboardInterrupt)")


if __name__ == "__main__":
    main()
