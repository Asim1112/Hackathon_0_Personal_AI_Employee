"""
gmail_watcher.py — Gmail Watcher for the Silver-tier AI Employee.

Polls Gmail for unread important emails every 120 seconds.
Creates a structured .md file in Needs_Action/ for each new message.

Architecture: Perception layer (Watcher) → Needs_Action/ → Claude (Reasoning) → Done/

Silver tier: HITL threshold is £50. New contacts always escalate to Pending_Approval/.
Typically started by scheduler.py at 8 AM daily.

Usage:
    python gmail_watcher.py
    python gmail_watcher.py --vault /path/to/silver --interval 120

    First run will open a browser for Google OAuth consent.
    Subsequent runs use the saved token.json automatically.

Dependencies (install via uv):
    uv sync
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

# ---------------------------------------------------------------------------
# Gmail OAuth scope — read-only is sufficient for a watcher
# ---------------------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# ---------------------------------------------------------------------------
# Keywords that auto-escalate priority from "high" → "urgent"
# ---------------------------------------------------------------------------
URGENT_KEYWORDS = {
    "urgent", "asap", "immediately", "critical", "deadline",
    "overdue", "legal", "lawsuit", "invoice overdue", "past due",
    "final notice", "action required", "time sensitive",
}


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for unread important messages and writes each one
    as a structured .md file into the vault's Needs_Action/ folder.

    Args:
        vault_path:       Root of the Obsidian vault (current directory).
        credentials_path: Path to credentials.json downloaded from Google Cloud Console.
                          Defaults to credentials.json in the vault root.
        check_interval:   Seconds between Gmail polls. Default 120.
    """

    def __init__(
        self,
        vault_path: str = ".",
        credentials_path: str | None = None,
        check_interval: int = 120,
    ):
        super().__init__(vault_path, check_interval)

        # Resolve credentials and token paths
        self.credentials_path = (
            Path(credentials_path)
            if credentials_path
            else self.vault_path / "credentials.json"
        )
        self.token_path = self.vault_path / "token.json"

        # State file persists processed IDs across restarts
        self.state_path = self.vault_path / ".gmail_watcher_state.json"
        self.processed_ids: set[str] = self._load_state()

        # Authenticate and build the Gmail API service
        self.service = self._authenticate()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _authenticate(self):
        """
        OAuth2 flow:
          1. Load existing token.json if present.
          2. Refresh expired token automatically.
          3. If no token, open browser for user consent and save token.json.
        """
        if not self.credentials_path.exists():
            self.logger.error(
                f"credentials.json not found at: {self.credentials_path}\n"
                "Download it from: https://console.cloud.google.com/ → "
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
                self.logger.info(
                    "No valid token found — launching browser for Google OAuth consent…"
                )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Persist the token so next run skips the browser
            self.token_path.write_text(creds.to_json(), encoding="utf-8")
            self.logger.info(f"Token saved to {self.token_path}")

        self.logger.info("Gmail API authenticated successfully.")
        return build("gmail", "v1", credentials=creds)

    # ------------------------------------------------------------------
    # State persistence (processed IDs survive restarts)
    # ------------------------------------------------------------------

    def _load_state(self) -> set[str]:
        """Load the set of already-processed Gmail message IDs from disk."""
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                ids = set(data.get("processed_ids", []))
                self.logger.info(f"Loaded {len(ids)} previously processed ID(s) from state.")
                return ids
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"Could not read state file ({e}), starting fresh.")
        return set()

    def _save_state(self) -> None:
        """Persist processed IDs to disk after every successful file creation."""
        self.state_path.write_text(
            json.dumps({"processed_ids": sorted(self.processed_ids)}, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # BaseWatcher interface — check_for_updates
    # ------------------------------------------------------------------

    def check_for_updates(self) -> list:
        """
        Query Gmail for unread important messages.
        Returns only messages not yet in processed_ids.
        """
        try:
            result = (
                self.service.users()
                .messages()
                .list(userId="me", q="is:unread is:important", maxResults=20)
                .execute()
            )
        except HttpError as e:
            self.logger.error(f"Gmail API error during list: {e}")
            return []

        messages = result.get("messages", [])
        new_messages = [m for m in messages if m["id"] not in self.processed_ids]

        self.logger.info(
            f"Gmail poll complete: {len(messages)} important unread, "
            f"{len(new_messages)} new."
        )
        return new_messages

    # ------------------------------------------------------------------
    # BaseWatcher interface — create_action_file
    # ------------------------------------------------------------------

    def create_action_file(self, message: dict) -> Path | None:
        """
        Fetch full message details from Gmail API and write a structured
        .md file to Needs_Action/.

        Frontmatter fields: type, gmail_id, thread_id, from, subject,
                            date_sent, received, priority, status, source.
        """
        msg_id = message["id"]

        # ---- Fetch full message ----
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
        except HttpError as e:
            self.logger.error(f"Failed to fetch message {msg_id}: {e}")
            return None

        # ---- Extract headers ----
        raw_headers = msg.get("payload", {}).get("headers", [])
        headers = {h["name"]: h["value"] for h in raw_headers}

        sender      = headers.get("From", "Unknown")
        subject     = headers.get("Subject", "(No Subject)")
        date_sent   = headers.get("Date", "")
        message_hdr = headers.get("Message-ID", "")
        thread_id   = msg.get("threadId", "")
        snippet     = msg.get("snippet", "")

        # ---- Extract body text ----
        body_text = self._extract_body(msg.get("payload", {}))
        body_preview = self._truncate(body_text or snippet, max_chars=2000)

        # ---- Determine priority ----
        priority = self._detect_priority(subject, body_text, snippet)

        # ---- Build filename ----
        date_slug    = datetime.now().strftime("%Y-%m-%d")
        subject_slug = self._slugify(subject, max_len=45)
        filename     = f"EMAIL_{date_slug}_{subject_slug}_{msg_id[:8]}.md"
        filepath     = self.needs_action / filename

        # ---- Timestamps ----
        received_iso = datetime.now(timezone.utc).isoformat()

        # ---- Write .md file ----
        content = f"""\
---
type: email
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
- [ ] Create follow-up task in Needs_Action
- [ ] Flag for human review (move to Pending_Approval if sensitive)
- [ ] Archive after processing (move file to Done/)

---

## Processing Notes

> _(Claude: add your analysis and action taken here before moving to Done/)_

---

*Captured by GmailWatcher at {received_iso}*
"""

        try:
            filepath.write_text(content, encoding="utf-8")
        except OSError as e:
            self.logger.error(f"Failed to write file {filename}: {e}")
            return None

        # ---- Mark as processed and persist state ----
        self.processed_ids.add(msg_id)
        self._save_state()

        self.logger.info(
            f"Created: {filename} | From: {sender[:50]} | Priority: {priority}"
        )
        return filepath

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------

    def _extract_body(self, payload: dict) -> str:
        """
        Recursively walk the Gmail message payload tree to find the
        first text/plain part and decode it from base64url.
        Falls back to text/html → strip tags if no plain text found.
        """
        mime_type = payload.get("mimeType", "")

        # Direct plain text part
        if mime_type == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace").strip()

        # Multipart: recurse into parts preferring plain before html
        if "parts" in payload:
            plain_fallback = ""
            for part in payload["parts"]:
                text = self._extract_body(part)
                if text and part.get("mimeType") == "text/plain":
                    return text
                if text and not plain_fallback:
                    plain_fallback = text
            return plain_fallback

        # HTML fallback: strip tags crudely
        if mime_type == "text/html":
            data = payload.get("body", {}).get("data", "")
            if data:
                html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                return re.sub(r"<[^>]+>", " ", html).strip()

        return ""

    def _detect_priority(self, subject: str, body: str, snippet: str) -> str:
        """
        Scan subject, body, and snippet for urgency keywords.
        Returns "urgent" or "high" (both are written as priority: <value>).
        """
        combined = f"{subject} {snippet} {body}".lower()
        if any(kw in combined for kw in URGENT_KEYWORDS):
            return "urgent"
        return "high"

    @staticmethod
    def _slugify(text: str, max_len: int = 45) -> str:
        """Convert a string to a safe, readable filename segment."""
        slug = re.sub(r"[^\w\s-]", "", text).strip()
        slug = re.sub(r"[\s_]+", "_", slug)
        return slug[:max_len].strip("_") or "email"

    @staticmethod
    def _truncate(text: str, max_chars: int = 2000) -> str:
        """Truncate long text with a clear marker."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n… *(truncated — see original in Gmail)*"

    @staticmethod
    def _escape_yaml(text: str) -> str:
        """Escape double quotes inside YAML string values."""
        return text.replace('"', '\\"')

    def shutdown(self) -> None:
        """Clean up the Gmail API HTTP connection on exit."""
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

    parser = argparse.ArgumentParser(
        description="GmailWatcher — Bronze AI Employee perception layer"
    )
    parser.add_argument(
        "--vault",
        default=".",
        help="Path to vault root (default: current directory)",
    )
    parser.add_argument(
        "--credentials",
        default=None,
        help="Path to credentials.json (default: <vault>/credentials.json)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=120,
        help="Seconds between Gmail polls (default: 120)",
    )
    args = parser.parse_args()

    watcher = GmailWatcher(
        vault_path=args.vault,
        credentials_path=args.credentials,
        check_interval=args.interval,
    )
    watcher.run()
