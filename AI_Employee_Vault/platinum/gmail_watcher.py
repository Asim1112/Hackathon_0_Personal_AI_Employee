"""
gmail_watcher.py — Gmail Watcher for the Platinum-tier AI Employee (Cloud Agent).

Platinum change: writes to Needs_Action/email/ instead of Needs_Action/.
All other logic identical to Gold tier.

Polls Gmail for unread important emails every 120 seconds.
Creates a structured .md file in Needs_Action/email/ for each new message.

Usage:
    python gmail_watcher.py
    python gmail_watcher.py --vault /path/to/platinum --interval 120
"""

import base64
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from base_watcher import BaseWatcher

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

URGENT_KEYWORDS = {
    "urgent", "asap", "immediately", "critical", "deadline",
    "overdue", "legal", "lawsuit", "invoice overdue", "past due",
    "final notice", "action required", "time sensitive",
}


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail and writes structured .md files to Needs_Action/email/.

    Platinum: sets needs_action_subdir="email" so all email items land in
    Needs_Action/email/ for Cloud Agent to claim via claim-by-move rule.
    """

    def __init__(
        self,
        vault_path: str = ".",
        credentials_path: str | None = None,
        check_interval: int = 120,
        needs_action_subdir: str = "email",   # Platinum: always "email"
    ):
        super().__init__(vault_path, check_interval, needs_action_subdir=needs_action_subdir)

        self.credentials_path = (
            Path(credentials_path) if credentials_path
            else self.vault_path / "credentials.json"
        )
        self.token_path  = self.vault_path / "token.json"
        self.state_path  = self.vault_path / ".gmail_watcher_state.json"
        self.processed_ids: set[str] = self._load_state()
        self.service = self._authenticate()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _authenticate(self):
        if not self.credentials_path.exists():
            self.logger.error(
                f"credentials.json not found at: {self.credentials_path}\n"
                "Download from: https://console.cloud.google.com/ → "
                "APIs & Services → Credentials → OAuth 2.0 Client IDs"
            )
            sys.exit(1)

        creds = None
        if self.token_path.exists():
            self.logger.info("Loading saved token from token.json")
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired access token…")
                creds.refresh(Request())
            else:
                self.logger.info("No valid token — launching OAuth consent…")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
            self.token_path.write_text(creds.to_json(), encoding="utf-8")
            self.logger.info(f"Token saved to {self.token_path}")

        self.logger.info("Gmail API authenticated.")
        return build("gmail", "v1", credentials=creds)

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _load_state(self) -> set[str]:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                ids = set(data.get("processed_ids", []))
                self.logger.info(f"Loaded {len(ids)} processed Gmail IDs from state.")
                return ids
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"Could not read state file ({e}), starting fresh.")
        return set()

    def _save_state(self) -> None:
        self.state_path.write_text(
            json.dumps({"processed_ids": sorted(self.processed_ids)}, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Poll
    # ------------------------------------------------------------------

    def check_for_updates(self) -> list:
        try:
            result = (
                self.service.users().messages()
                .list(userId="me", q="is:unread is:important", maxResults=20)
                .execute()
            )
        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}")
            return []

        messages = result.get("messages", [])
        new = [m for m in messages if m["id"] not in self.processed_ids]
        self.logger.info(f"Gmail poll: {len(messages)} unread important, {len(new)} new.")
        return new

    # ------------------------------------------------------------------
    # File creation — writes to Needs_Action/email/
    # ------------------------------------------------------------------

    def create_action_file(self, message: dict) -> Path | None:
        msg_id = message["id"]
        try:
            msg = (
                self.service.users().messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
        except HttpError as e:
            self.logger.error(f"Failed to fetch message {msg_id}: {e}")
            return None

        raw_headers  = msg.get("payload", {}).get("headers", [])
        headers      = {h["name"]: h["value"] for h in raw_headers}
        sender       = headers.get("From", "Unknown")
        subject      = headers.get("Subject", "(No Subject)")
        date_sent    = headers.get("Date", "")
        message_hdr  = headers.get("Message-ID", "")
        thread_id    = msg.get("threadId", "")
        snippet      = msg.get("snippet", "")
        body_text    = self._extract_body(msg.get("payload", {}))
        body_preview = self._truncate(body_text or snippet, max_chars=2000)
        priority     = self._detect_priority(subject, body_text, snippet)

        date_slug    = datetime.now().strftime("%Y-%m-%d")
        subject_slug = self._slugify(subject, max_len=45)
        filename     = f"EMAIL_{date_slug}_{subject_slug}_{msg_id[:8]}.md"
        filepath     = self.needs_action / filename  # → Needs_Action/email/<filename>
        received_iso = datetime.now(timezone.utc).isoformat()

        content = f"""\
---
type: email
agent_target: cloud_agent
gmail_id: "{msg_id}"
thread_id: "{thread_id}"
message_id_header: "{message_hdr}"
from: "{self._escape_yaml(sender)}"
subject: "{self._escape_yaml(subject)}"
date_sent: "{date_sent}"
received: "{received_iso}"
priority: {priority}
status: pending
source: gmail
---

# {subject}

**From:** {sender}
**Date:** {date_sent}
**Subject:** {subject}

---

## Email Body

{body_preview}

---

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Log as project or client update
- [ ] Flag for human review (move to Pending_Approval/email/ if sensitive)
- [ ] Archive after processing (move to Done/)

---

## Processing Notes

> _(Cloud Agent: add analysis and action taken here)_
> _(Write draft reply to Pending_Approval/email/ — do NOT send directly)_

---

*Captured by GmailWatcher (Platinum/Cloud) at {received_iso}*
"""
        try:
            filepath.write_text(content, encoding="utf-8")
        except OSError as e:
            self.logger.error(f"Failed to write file {filename}: {e}")
            return None

        self.processed_ids.add(msg_id)
        self._save_state()
        self.logger.info(f"Created: {filename} | From: {sender[:50]} | Priority: {priority}")
        return filepath

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_body(self, payload: dict) -> str:
        mime_type = payload.get("mimeType", "")
        if mime_type == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace").strip()
        if "parts" in payload:
            plain_fallback = ""
            for part in payload["parts"]:
                text = self._extract_body(part)
                if text and part.get("mimeType") == "text/plain":
                    return text
                if text and not plain_fallback:
                    plain_fallback = text
            return plain_fallback
        if mime_type == "text/html":
            data = payload.get("body", {}).get("data", "")
            if data:
                html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                return re.sub(r"<[^>]+>", " ", html).strip()
        return ""

    def _detect_priority(self, subject: str, body: str, snippet: str) -> str:
        combined = f"{subject} {snippet} {body}".lower()
        return "urgent" if any(kw in combined for kw in URGENT_KEYWORDS) else "high"

    @staticmethod
    def _slugify(text: str, max_len: int = 45) -> str:
        slug = re.sub(r"[^\w\s-]", "", text).strip()
        slug = re.sub(r"[\s_]+", "_", slug)
        return slug[:max_len].strip("_") or "email"

    @staticmethod
    def _truncate(text: str, max_chars: int = 2000) -> str:
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n… *(truncated — see original in Gmail)*"

    @staticmethod
    def _escape_yaml(text: str) -> str:
        return text.replace('"', '\\"')

    def shutdown(self) -> None:
        try:
            self.service.close()
        except Exception:
            pass
        self.logger.info("Gmail API connection closed.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv

    parser = argparse.ArgumentParser(description="GmailWatcher — Platinum Cloud Agent")
    parser.add_argument("--vault",       default=".",  help="Vault root")
    parser.add_argument("--credentials", default=None, help="Path to credentials.json")
    parser.add_argument("--interval",    type=int, default=120, help="Poll interval (s)")
    args = parser.parse_args()

    load_dotenv(Path(args.vault) / ".env")

    watcher = GmailWatcher(
        vault_path=args.vault,
        credentials_path=args.credentials,
        check_interval=args.interval,
        needs_action_subdir="email",
    )
    watcher.run()
