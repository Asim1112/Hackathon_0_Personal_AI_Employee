"""
scheduler.py — Daily 8 AM Scheduler for the Silver-tier AI Employee.

Starts all three watchers (Gmail + LinkedIn + WhatsApp) and triggers the
Claude processing loop every day at 8:00 AM local time.

Can also be invoked directly to run an immediate one-shot cycle.

Architecture:
    OS cron / Windows Task Scheduler → scheduler.py
    scheduler.py → gmail_watcher.py (continuous, background thread)
    scheduler.py → linkedin_watcher.py (continuous, background thread)
    scheduler.py → whatsapp_watcher.py (continuous, background thread)
    scheduler.py → claude --print (daily 8 AM reasoning cycle)

Usage:
    # Run continuously (starts watchers + schedules daily Claude run)
    python scheduler.py

    # Run immediate one-shot Claude cycle (for testing)
    python scheduler.py --now

    # Run with custom vault path
    python scheduler.py --vault /path/to/silver

Dependencies:
    uv sync  (includes schedule, python-dotenv)

Windows Task Scheduler setup:
    Program:   uv
    Arguments: run python scheduler.py
    Start in:  <path-to-silver-vault>
    Trigger:   Daily at 08:00

Linux/macOS cron:
    0 8 * * 1-6 cd /path/to/silver && uv run python scheduler.py --now
"""

import argparse
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import schedule
from dotenv import load_dotenv

# Load .env from vault root
VAULT_PATH = Path(__file__).parent.resolve()
load_dotenv(VAULT_PATH / ".env")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [scheduler     ] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("scheduler")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CLAUDE_PROMPT = """Read CLAUDE.md then:
1. Use SKILL_Daily_Briefing to generate the morning briefing.
2. Use SKILL_Gmail_Triage to triage all emails in Needs_Action/.
3. Use SKILL_LinkedIn_Draft for any linkedin_opportunity items.
4. Use SKILL_Reasoning_Loop for any complex multi-step tasks.
5. Use SKILL_Process_Needs_Action to process all pending items.
6. Use SKILL_Update_Dashboard to refresh Dashboard.md.
Output TASK_COMPLETE when Needs_Action/ is empty."""

GMAIL_INTERVAL_S     = int(os.getenv("GMAIL_INTERVAL",     "120"))
LINKEDIN_INTERVAL_S  = int(os.getenv("LINKEDIN_INTERVAL",  "300"))
WHATSAPP_INTERVAL_S  = int(os.getenv("WHATSAPP_INTERVAL",  "30"))
HEADLESS             = os.getenv("HEADLESS", "true").lower() != "false"

# ---------------------------------------------------------------------------
# Claude runner
# ---------------------------------------------------------------------------

def run_claude_cycle(vault_path: Path) -> None:
    """Invoke Claude Code with the daily processing prompt."""
    log.info("Starting daily Claude processing cycle...")
    cmd = ["claude", "--print", CLAUDE_PROMPT]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(vault_path),
            capture_output=False,
            text=True,
            timeout=600,  # 10-minute max
        )
        if result.returncode == 0:
            log.info("Claude cycle completed successfully")
        else:
            log.error(f"Claude cycle exited with code {result.returncode}")
    except FileNotFoundError:
        log.error("'claude' command not found. Is Claude Code installed and in PATH?")
    except subprocess.TimeoutExpired:
        log.error("Claude cycle timed out after 10 minutes")
    except Exception as e:
        log.error(f"Claude cycle error: {e}", exc_info=True)

# ---------------------------------------------------------------------------
# Watcher threads
# ---------------------------------------------------------------------------

def start_gmail_watcher(vault_path: Path) -> threading.Thread:
    """Start the Gmail watcher in a background daemon thread."""
    def run():
        log.info(f"Gmail watcher starting (interval: {GMAIL_INTERVAL_S}s)")
        try:
            # Import and run inline to stay in the same process
            sys.path.insert(0, str(vault_path))
            from gmail_watcher import GmailWatcher
            watcher = GmailWatcher(
                vault_path=str(vault_path),
                check_interval=GMAIL_INTERVAL_S,
            )
            watcher.run()
        except Exception as e:
            log.error(f"Gmail watcher crashed: {e}", exc_info=True)

    t = threading.Thread(target=run, name="GmailWatcher", daemon=True)
    t.start()
    log.info("Gmail watcher thread started")
    return t


def start_linkedin_watcher(vault_path: Path) -> threading.Thread:
    """Start the LinkedIn watcher in a background daemon thread."""
    def run():
        log.info(f"LinkedIn watcher starting (interval: {LINKEDIN_INTERVAL_S}s)")
        try:
            sys.path.insert(0, str(vault_path))
            from linkedin_watcher import LinkedInWatcher
            watcher = LinkedInWatcher(
                vault_path=str(vault_path),
                check_interval=LINKEDIN_INTERVAL_S,
                headless=HEADLESS,
            )
            watcher.run()
        except Exception as e:
            log.error(f"LinkedIn watcher crashed: {e}", exc_info=True)

    t = threading.Thread(target=run, name="LinkedInWatcher", daemon=True)
    t.start()
    log.info("LinkedIn watcher thread started")
    return t


def start_whatsapp_watcher(vault_path: Path) -> threading.Thread:
    """
    Start the WhatsApp watcher in a background daemon thread.

    NOTE: WhatsApp Web requires a persistent context (browser session stored
    on disk). The first run MUST be done manually with --no-headless to scan
    the QR code. Once scanned, the session is saved to whatsapp_session/ and
    this thread can run headlessly on all subsequent starts.
    """
    def run():
        log.info(f"WhatsApp watcher starting (interval: {WHATSAPP_INTERVAL_S}s)")
        session_dir = vault_path / "whatsapp_session"
        if not session_dir.exists():
            log.warning(
                "whatsapp_session/ not found. WhatsApp watcher needs a first-run QR scan.\n"
                "  Run: uv run python whatsapp_watcher.py --no-headless\n"
                "  Scan the QR code, then Ctrl-C and restart the scheduler."
            )
            return
        try:
            sys.path.insert(0, str(vault_path))
            from whatsapp_watcher import WhatsAppWatcher
            watcher = WhatsAppWatcher(
                vault_path=str(vault_path),
                session_path=str(session_dir),
                check_interval=WHATSAPP_INTERVAL_S,
                headless=HEADLESS,
            )
            watcher.run()
        except Exception as e:
            log.error(f"WhatsApp watcher crashed: {e}", exc_info=True)

    t = threading.Thread(target=run, name="WhatsAppWatcher", daemon=True)
    t.start()
    log.info("WhatsApp watcher thread started")
    return t

# ---------------------------------------------------------------------------
# Main scheduler loop
# ---------------------------------------------------------------------------

def main(vault_path: Path, run_now: bool = False) -> None:
    log.info("=" * 60)
    log.info("AI Employee Scheduler — Silver Tier")
    log.info(f"Vault: {vault_path}")
    log.info("=" * 60)

    # Check for required credentials
    if not (vault_path / "credentials.json").exists():
        log.warning(
            "credentials.json not found — Gmail watcher will fail. "
            "See README.md for Google Cloud Console setup."
        )

    li_email = os.getenv("LINKEDIN_EMAIL")
    if not li_email:
        log.warning(
            "LINKEDIN_EMAIL not set in .env — LinkedIn watcher will not start."
        )

    wa_session = vault_path / "whatsapp_session"
    if not wa_session.exists():
        log.warning(
            "whatsapp_session/ not found — WhatsApp watcher will not start. "
            "Run: uv run python whatsapp_watcher.py --no-headless  (scan QR first)"
        )

    # Start watchers in background threads
    gmail_thread     = start_gmail_watcher(vault_path)
    linkedin_thread  = None
    whatsapp_thread  = None

    if li_email:
        linkedin_thread = start_linkedin_watcher(vault_path)

    if wa_session.exists():
        whatsapp_thread = start_whatsapp_watcher(vault_path)

    # Run an immediate cycle if requested
    if run_now:
        log.info("--now flag set: running immediate Claude cycle")
        run_claude_cycle(vault_path)

    # Schedule daily 8 AM Claude cycle
    schedule.every().day.at("08:00").do(run_claude_cycle, vault_path=vault_path)
    log.info("Scheduled: Claude processing cycle daily at 08:00")

    # Main loop — runs the schedule and monitors watcher threads
    log.info("Scheduler running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()

            # Log watcher health every 5 minutes
            if int(time.time()) % 300 < 5:
                gmail_status    = "✅ alive" if gmail_thread.is_alive() else "❌ dead"
                linkedin_status = (
                    "✅ alive" if (linkedin_thread and linkedin_thread.is_alive())
                    else ("❌ dead" if linkedin_thread else "⚪ not started")
                )
                whatsapp_status = (
                    "✅ alive" if (whatsapp_thread and whatsapp_thread.is_alive())
                    else ("❌ dead" if whatsapp_thread else "⚪ not started")
                )
                log.info(
                    f"Watcher health — Gmail: {gmail_status} | "
                    f"LinkedIn: {linkedin_status} | WhatsApp: {whatsapp_status}"
                )

            time.sleep(5)

    except KeyboardInterrupt:
        log.info("Scheduler stopping (KeyboardInterrupt)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Silver AI Employee Scheduler — starts watchers and runs daily Claude cycle"
    )
    parser.add_argument(
        "--vault", default=".", help="Path to vault root (default: current directory)"
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run an immediate Claude cycle on startup (in addition to daily 8 AM)",
    )
    args = parser.parse_args()

    main(vault_path=Path(args.vault).resolve(), run_now=args.now)
