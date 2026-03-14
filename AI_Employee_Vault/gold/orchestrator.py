"""
orchestrator.py — Gold AI Employee Orchestrator

Starts all 6 watchers as daemon threads, supervises them with a watchdog
that auto-restarts any that crash, and fires the Claude reasoning loop on schedule:

  - Daily at 08:00   → full triage cycle (email, WhatsApp, LinkedIn, Twitter, FB/IG, Odoo)
  - Sunday at 23:00  → weekly CEO briefing (Odoo sync + social analytics + Done/ summary)

Modes:
  python orchestrator.py              daemon: watchers + daily/weekly schedules
  python orchestrator.py --now        daemon + immediate Claude run on startup
  python orchestrator.py --cron       one-shot: run daily Claude cycle once and exit
  python orchestrator.py --briefing   one-shot: run weekly CEO briefing once and exit

Cron fallback (add to Task Scheduler / crontab):
  Daily:   0 8 * * 1-6  cd /path/to/gold && uv run python orchestrator.py --cron
  Weekly:  0 23 * * 0   cd /path/to/gold && uv run python orchestrator.py --briefing

Dependencies (all in pyproject.toml — run `uv sync` to install):
  schedule>=1.2.0, python-dotenv>=1.0.0
  Plus watcher deps: tweepy, httpx, requests, playwright, google-api-python-client

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

# Daily triage prompt — covers all 6 channels
DAILY_PROMPT = (
    "Read CLAUDE.md then run the Standard Daily Workflow: "
    "SKILL_Daily_Briefing → SKILL_Gmail_Triage → SKILL_WhatsApp_Triage → "
    "SKILL_LinkedIn_Draft → SKILL_Twitter_Draft → SKILL_Facebook_Instagram → "
    "SKILL_Odoo_Accounting → SKILL_Reasoning_Loop → SKILL_Process_Needs_Action → "
    "SKILL_Audit_Logger → SKILL_Update_Dashboard. "
    "Write TASK_COMPLETE when Needs_Action/ is empty."
)

# Weekly CEO briefing prompt — runs every Sunday at 23:00
WEEKLY_BRIEFING_PROMPT = (
    "Read CLAUDE.md then run the Standard Weekly Workflow: "
    "SKILL_Weekly_CEO_Briefing → SKILL_Update_Dashboard → SKILL_Audit_Logger. "
    "Write TASK_COMPLETE when the briefing is saved to Briefings/."
)

WATCHDOG_INTERVAL = 30    # seconds between thread health checks
CLAUDE_TIMEOUT    = 900   # 15-minute cap per Claude cycle (Gold has more work)

# ── Watcher registry ──────────────────────────────────────────────────────────

def _watcher_registry(vault: Path) -> list:
    iv = lambda k, d: int(os.getenv(k, d))
    hl = os.getenv("HEADLESS", "true").lower() != "false"

    def gmail():
        sys.path.insert(0, str(vault))
        from gmail_watcher import GmailWatcher
        GmailWatcher(vault_path=str(vault),
                     check_interval=iv("GMAIL_INTERVAL", "120")).run()

    def linkedin():
        sys.path.insert(0, str(vault))
        from linkedin_watcher import LinkedInWatcher
        LinkedInWatcher(vault_path=str(vault),
                        check_interval=iv("LINKEDIN_INTERVAL", "300"),
                        headless=hl).run()

    def whatsapp():
        sys.path.insert(0, str(vault))
        from whatsapp_watcher import WhatsAppWatcher
        WhatsAppWatcher(vault_path=str(vault),
                        session_path=str(vault / "whatsapp_session"),
                        check_interval=iv("WHATSAPP_INTERVAL", "30"),
                        headless=hl).run()

    def twitter():
        sys.path.insert(0, str(vault))
        from twitter_watcher import TwitterWatcher
        TwitterWatcher(vault_path=str(vault),
                       check_interval=iv("TWITTER_INTERVAL", "300")).run()

    def facebook():
        sys.path.insert(0, str(vault))
        from facebook_watcher import FacebookWatcher
        FacebookWatcher(vault_path=str(vault),
                        check_interval=iv("FACEBOOK_INTERVAL", "600")).run()

    def odoo():
        sys.path.insert(0, str(vault))
        from odoo_watcher import OdooWatcher
        OdooWatcher(vault_path=str(vault),
                    check_interval=iv("ODOO_INTERVAL", "600")).run()

    return [
        # (display_name, guard_fn, target_fn)
        ("Gmail",
         lambda: (vault / "credentials.json").exists(),
         gmail),
        ("LinkedIn",
         lambda: bool(os.getenv("LINKEDIN_EMAIL")) and bool(os.getenv("LINKEDIN_PASSWORD")),
         linkedin),
        ("WhatsApp",
         lambda: (vault / "whatsapp_session").exists(),
         whatsapp),
        ("Twitter",
         lambda: bool(os.getenv("TWITTER_BEARER_TOKEN")),
         twitter),
        ("Facebook",
         lambda: bool(os.getenv("FACEBOOK_ACCESS_TOKEN")) and bool(os.getenv("FACEBOOK_PAGE_ID")),
         facebook),
        ("Odoo",
         lambda: bool(os.getenv("ODOO_PASSWORD")) and os.getenv("ODOO_PASSWORD") != "your-odoo-admin-password",
         odoo),
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


def run_claude(vault: Path, prompt: str = DAILY_PROMPT) -> None:
    log.info("Claude reasoning cycle starting…")
    cmd = _find_claude() + ["--dangerously-skip-permissions", "--print", prompt]
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


def run_daily(vault: Path) -> None:
    log.info("Triggering daily triage cycle")
    run_claude(vault, DAILY_PROMPT)


def run_weekly_briefing(vault: Path) -> None:
    log.info("Triggering weekly CEO briefing")
    run_claude(vault, WEEKLY_BRIEFING_PROMPT)

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
    Start all watchers whose guards pass, then restart any that die.
    Runs in its own daemon thread.
    """
    registry = _watcher_registry(vault)
    threads: dict[str, threading.Thread] = {}

    for name, guard, fn in registry:
        if guard():
            threads[name] = _spawn(name, fn)
        else:
            log.warning(
                f"{name} watcher skipped — prerequisite missing "
                f"(check .env / credentials / session files)"
            )

    while True:
        time.sleep(WATCHDOG_INTERVAL)
        for name, guard, fn in registry:
            t = threads.get(name)
            if t is not None and not t.is_alive():
                log.warning(f"{name} watcher is dead — restarting…")
                threads[name] = _spawn(name, fn)

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Gold AI Employee Orchestrator")
    parser.add_argument("--vault",     default=".", help="Vault root (default: current dir)")
    parser.add_argument("--now",       action="store_true", help="Run daily Claude cycle immediately on startup")
    parser.add_argument("--cron",      action="store_true", help="One-shot: run daily cycle once then exit")
    parser.add_argument("--briefing",  action="store_true", help="One-shot: run weekly CEO briefing once then exit")
    args = parser.parse_args()

    vault = Path(args.vault).resolve()
    log.info(f"Gold AI Employee Orchestrator | Vault: {vault}")

    # ── One-shot modes ────────────────────────────────────────────────────────
    if args.cron:
        log.info("Cron mode — running daily triage cycle then exiting")
        run_daily(vault)
        return

    if args.briefing:
        log.info("Briefing mode — running weekly CEO briefing then exiting")
        run_weekly_briefing(vault)
        return

    # ── Daemon mode ───────────────────────────────────────────────────────────
    if args.now:
        run_daily(vault)

    # Watchdog runs in background; schedule loop runs in main thread
    threading.Thread(target=run_watchdog, args=(vault,), name="Watchdog", daemon=True).start()

    # Daily triage at 08:00
    schedule.every().day.at("08:00").do(run_daily, vault=vault)
    # Weekly CEO briefing every Sunday at 23:00
    schedule.every().sunday.at("23:00").do(run_weekly_briefing, vault=vault)

    log.info(
        "Scheduled: Daily triage at 08:00 | "
        "Weekly CEO Briefing every Sunday at 23:00 | "
        "Watchdog active (6 watchers)"
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        log.info("Orchestrator stopped (KeyboardInterrupt)")


if __name__ == "__main__":
    main()
