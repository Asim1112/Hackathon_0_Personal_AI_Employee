"""
email_sender.py — Platinum Local Agent Email Sender

Watches platinum/Approved/ for .md files and processes them:
  type: draft_reply       → send email via Gmail API → Done/
  type: approval_request  → acknowledge + archive     → Done/
  other                   → archive with note         → Done/

Usage:
  uv run python email_sender.py           # daemon (polls every 10s)
  uv run python email_sender.py --once    # process current files then exit

Credentials: looks for credentials.json + token.json in platinum/ first,
             then falls back to AI_Employee_Vault/ root.
"""

import argparse
import base64
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ── Paths ─────────────────────────────────────────────────────────────────────

VAULT = Path(__file__).parent.resolve()
load_dotenv(VAULT / ".env")

# Must match the scopes used when token.json was generated.
# gmail.readonly (for watcher) + gmail.send (for sender).
SCOPES        = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
POLL_INTERVAL = 10   # seconds

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [email-sender] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("email_sender")

# ── Credential helpers ────────────────────────────────────────────────────────

def _find_file(name: str) -> Path | None:
    """Find a credential file — check platinum/ first, then vault root."""
    for candidate in (VAULT / name, VAULT.parent / name):
        if candidate.exists():
            return candidate
    return None


def run_auth_flow() -> None:
    """
    Run the OAuth2 consent flow in a local browser and save token.json.
    Run this once on Windows before starting the sender daemon:
        uv run python email_sender.py --auth-only
    """
    creds_path = _find_file("credentials.json")
    if not creds_path:
        log.error("credentials.json not found in platinum/ or vault root — cannot start OAuth flow")
        return

    token_dest = VAULT / "token.json"
    log.info("Starting OAuth flow — a browser window will open for Google sign-in…")
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)
    token_dest.write_text(creds.to_json(), encoding="utf-8")
    log.info("✓ token.json saved to %s", token_dest)
    log.info("  Granted scopes: %s", creds.scopes)
    log.info("Now you can start the sender: uv run python email_sender.py")


def get_gmail_service():
    """Return authenticated Gmail API service, refreshing token if needed."""
    token_path = _find_file("token.json")

    if not token_path:
        log.error(
            "token.json not found. Run OAuth flow first:\n"
            "  uv run python email_sender.py --auth-only"
        )
        return None

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log.info("Refreshing Gmail token…")
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
            log.info("Token refreshed")
        else:
            log.error(
                "Gmail token is invalid and cannot be refreshed.\n"
                "Re-run the OAuth flow:\n"
                "  uv run python email_sender.py --auth-only"
            )
            return None

    # Verify that gmail.send scope is included in this token
    if creds.scopes and "https://www.googleapis.com/auth/gmail.send" not in creds.scopes:
        log.error(
            "Token is missing gmail.send scope. Delete token.json and re-run:\n"
            "  del platinum\\token.json\n"
            "  uv run python email_sender.py --auth-only"
        )
        return None

    return build("gmail", "v1", credentials=creds)

# ── Frontmatter parser ────────────────────────────────────────────────────────

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML-style frontmatter. Returns (meta_dict, body_text)."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)", content, re.DOTALL)
    if not m:
        return {}, content
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([\w_-]+):\s*(.+?)\s*$", line)
        if kv:
            # strip surrounding quotes
            meta[kv.group(1)] = kv.group(2).strip('"').strip("'")
    return meta, m.group(2).strip()

# ── Audit log ─────────────────────────────────────────────────────────────────

def log_action(action: str, file_name: str, details: dict) -> None:
    """Append an entry to today's Logs/YYYY-MM-DD.json."""
    log_dir = VAULT / "Logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "local_agent",
        "action": action,
        "file": file_name,
        **details,
    }

    entries: list = []
    if log_file.exists():
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
            if not isinstance(entries, list):
                entries = []
        except Exception:
            entries = []

    entries.append(entry)
    log_file.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")

# ── File move helper ──────────────────────────────────────────────────────────

def move_to_done(src: Path, original_content: str, note: str) -> None:
    """Update status field and move src → Done/ with appended note."""
    done_dir = VAULT / "Done"
    done_dir.mkdir(exist_ok=True)

    updated = re.sub(r"^(status:\s*)pending\s*$", r"\1done", original_content,
                     flags=re.MULTILINE)
    updated += f"\n\n---\n\n**{note}**\n"

    dest = done_dir / src.name
    dest.write_text(updated, encoding="utf-8")
    src.unlink()
    log.info("Archived → Done/%s", src.name)

# ── Gmail send ────────────────────────────────────────────────────────────────

def send_gmail(service, to: str, subject: str, body: str, sender: str) -> str:
    """Send via Gmail API. Returns Gmail message ID."""
    msg = MIMEText(body, "plain")
    msg["to"]      = to
    msg["from"]    = sender
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
    return result.get("id", "unknown")

# ── Core processor ────────────────────────────────────────────────────────────

def process_file(f: Path) -> None:
    """Process one .md file from Approved/ based on its type field."""
    log.info("─── Processing: %s", f.name)

    try:
        content = f.read_text(encoding="utf-8")
    except Exception as e:
        log.error("Could not read %s: %s", f.name, e)
        return

    meta, body = parse_frontmatter(content)
    file_type  = meta.get("type", "unknown")
    now_iso    = datetime.now(timezone.utc).isoformat()

    # ── draft_reply: send email ───────────────────────────────────────────────
    if file_type == "draft_reply":
        to      = meta.get("to", "").strip()
        subject = meta.get("subject", "(no subject)")
        sender  = os.getenv("GMAIL_ADDRESS", "")

        if not to:
            log.warning("draft_reply has no 'to' field — archiving without send")
            move_to_done(f, content,
                         f"WARNING: No recipient address — email NOT sent ({now_iso})")
            log_action("email_skipped", f.name,
                       {"reason": "no_recipient", "subject": subject})
            return

        service = get_gmail_service()
        if not service:
            log.error("Gmail service unavailable — will retry next poll cycle")
            return  # leave file in Approved/ to retry

        try:
            msg_id = send_gmail(service, to, subject, body, sender)
            note   = f"Sent {now_iso} · Gmail messageId: {msg_id}"
            move_to_done(f, content, note)
            log_action("email_sent", f.name,
                       {"to": to, "subject": subject, "gmail_id": msg_id})
            log.info("✓ Email sent → %s | %s", to, subject)
        except HttpError as e:
            log.error("Gmail API error: %s", e)
            log_action("email_failed", f.name,
                       {"to": to, "subject": subject, "error": str(e)})

    # ── approval_request: acknowledge + archive ───────────────────────────────
    elif file_type == "approval_request":
        from_  = meta.get("from", "unknown sender")
        subject = meta.get("subject", "(no subject)")
        note   = f"Acknowledged by Local Agent {now_iso} — informational, no reply sent"
        move_to_done(f, content, note)
        log_action("email_acknowledged", f.name,
                   {"from": from_, "subject": subject})
        log.info("✓ Acknowledged: [%s] from %s", subject, from_)

    # ── anything else ─────────────────────────────────────────────────────────
    else:
        note = f"Processed by Local Agent {now_iso} (type: {file_type})"
        move_to_done(f, content, note)
        log_action("file_processed", f.name, {"type": file_type})
        log.info("✓ Archived (type=%s): %s", file_type, f.name)

# ── Watcher loop ──────────────────────────────────────────────────────────────

def watch_approved(once: bool = False) -> None:
    """
    Poll Approved/ every POLL_INTERVAL seconds.
    Called directly or imported by local_orchestrator as a daemon thread.
    """
    approved = VAULT / "Approved"
    approved.mkdir(exist_ok=True)
    seen: set[str] = set()

    log.info("Watching %s (every %ds)", approved, POLL_INTERVAL)

    while True:
        try:
            for f in sorted(approved.glob("*.md")):
                if f.name not in seen:
                    seen.add(f.name)
                    process_file(f)
                    # Re-check: file may have been moved to Done/
                    if not f.exists():
                        pass  # successfully processed
                    # If still in Approved/ (e.g. Gmail auth failed), keep in seen
                    # so we don't spam retries — clear on next restart
        except Exception as e:
            log.error("Watcher error: %s", e)

        if once:
            break
        time.sleep(POLL_INTERVAL)

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Platinum Email Sender — Local Agent")
    parser.add_argument(
        "--once", action="store_true",
        help="Process all files currently in Approved/ then exit"
    )
    parser.add_argument(
        "--auth-only", action="store_true",
        help="Run OAuth2 consent flow to create/refresh token.json, then exit"
    )
    args = parser.parse_args()

    log.info("Platinum Email Sender | Vault: %s | Agent: local_agent", VAULT)

    if args.auth_only:
        run_auth_flow()
        return

    creds_path = _find_file("credentials.json")
    token_path = _find_file("token.json")
    log.info(
        "Credentials: %s | Token: %s",
        creds_path or "NOT FOUND",
        token_path or "NOT FOUND",
    )

    watch_approved(once=args.once)


if __name__ == "__main__":
    main()
