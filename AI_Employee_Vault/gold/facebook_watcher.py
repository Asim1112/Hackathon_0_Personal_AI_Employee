"""
facebook_watcher.py — Facebook & Instagram Watcher for the Gold-tier AI Employee.

Polls via Meta Graph API for:
  - New Facebook Page messages (DMs from visitors)
  - New Facebook Page post comments
  - New Instagram Business account comments
  - Instagram direct messages (if permissions allow)
  - Page/account follower/likes count changes

Creates structured .md files in Needs_Action/ for Claude to process.

State is persisted in .facebook_watcher_state.json.

Requirements:
  - A Facebook Developer App with pages_messaging, pages_read_engagement,
    instagram_manage_comments, instagram_manage_insights permissions
  - A long-lived Page Access Token (never expires, unlike short-lived user tokens)

Usage:
    python facebook_watcher.py
    python facebook_watcher.py --vault /path/to/gold --interval 600

Dependencies (install via uv):
    uv sync
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

from base_watcher import BaseWatcher
from audit_logger import log_action, log_watcher_start, log_watcher_stop, log_error

# ---------------------------------------------------------------------------
# Meta Graph API base
# ---------------------------------------------------------------------------
GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
STATE_FILE_NAME = ".facebook_watcher_state.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_state(vault_path: Path) -> dict:
    state_file = vault_path / STATE_FILE_NAME
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "last_message_time": None,
        "last_comment_time": None,
        "last_ig_comment_time": None,
        "last_page_fan_count": 0,
        "last_ig_follower_count": 0,
        "seen_message_ids": [],
        "seen_comment_ids": [],
    }


def _save_state(vault_path: Path, state: dict) -> None:
    # Keep seen ID lists bounded to avoid file bloat
    state["seen_message_ids"] = state["seen_message_ids"][-200:]
    state["seen_comment_ids"] = state["seen_comment_ids"][-200:]
    state_file = vault_path / STATE_FILE_NAME
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Watcher class
# ---------------------------------------------------------------------------

class FacebookWatcher(BaseWatcher):
    """Polls Meta Graph API for Facebook Page and Instagram activity."""

    def __init__(self, vault_path: str, check_interval: int = 600):
        super().__init__(vault_path, check_interval)
        self.state = _load_state(self.vault_path)

        self.page_id     = os.environ.get("FACEBOOK_PAGE_ID", "")
        self.page_token  = os.environ.get("FACEBOOK_ACCESS_TOKEN", "")
        self.ig_id       = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")

        if not self.page_token or not self.page_id:
            self.logger.error(
                "Missing FACEBOOK_PAGE_ID or FACEBOOK_ACCESS_TOKEN in .env"
            )
            sys.exit(1)

        self._http = httpx.Client(timeout=30.0)

    # ------------------------------------------------------------------
    # Graph API helpers
    # ------------------------------------------------------------------

    def _graph_get(self, path: str, params: dict | None = None) -> dict:
        """Make a GET request to the Graph API and return the JSON response."""
        full_params = {"access_token": self.page_token}
        if params:
            full_params.update(params)
        resp = self._http.get(f"{GRAPH_API_BASE}/{path}", params=full_params)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Poll
    # ------------------------------------------------------------------

    def check_for_updates(self) -> list[dict]:
        """Poll Facebook/Instagram for new events."""
        items: list[dict] = []

        try:
            items.extend(self._poll_page_messages())
        except Exception as exc:
            self.logger.warning("Page messages poll failed: %s", exc)
            log_error("facebook_watcher", "page_messages", str(exc))

        try:
            items.extend(self._poll_page_comments())
        except Exception as exc:
            self.logger.warning("Page comments poll failed: %s", exc)
            log_error("facebook_watcher", "page_comments", str(exc))

        if self.ig_id:
            try:
                items.extend(self._poll_ig_comments())
            except Exception as exc:
                self.logger.warning("Instagram comments poll failed: %s", exc)
                log_error("facebook_watcher", "ig_comments", str(exc))

        try:
            follower_item = self._check_follower_counts()
            if follower_item:
                items.append(follower_item)
        except Exception as exc:
            self.logger.warning("Follower count check failed: %s", exc)

        _save_state(self.vault_path, self.state)
        return items

    def _poll_page_messages(self) -> list[dict]:
        """Fetch new messages to the Facebook Page inbox."""
        data = self._graph_get(
            f"{self.page_id}/conversations",
            {"fields": "messages{id,created_time,message,from}", "limit": 10},
        )
        items = []
        conversations = data.get("data", [])

        for conv in conversations:
            messages = conv.get("messages", {}).get("data", [])
            for msg in messages:
                msg_id = msg.get("id")
                if msg_id in self.state["seen_message_ids"]:
                    continue

                # Skip messages sent by the Page itself
                sender = msg.get("from", {})
                if str(sender.get("id")) == str(self.page_id):
                    self.state["seen_message_ids"].append(msg_id)
                    continue

                items.append({
                    "event_type": "fb_message",
                    "id": msg_id,
                    "sender_name": sender.get("name", "Unknown"),
                    "sender_id": str(sender.get("id", "")),
                    "text": msg.get("message", ""),
                    "created_time": msg.get("created_time", datetime.now(timezone.utc).isoformat()),
                })
                self.state["seen_message_ids"].append(msg_id)

        if items:
            self.logger.info("Found %d new FB message(s)", len(items))
        return items

    def _poll_page_comments(self) -> list[dict]:
        """Fetch recent comments on Page posts."""
        data = self._graph_get(
            f"{self.page_id}/feed",
            {"fields": "comments{id,created_time,message,from}", "limit": 5},
        )
        items = []
        posts = data.get("data", [])

        for post in posts:
            comments = post.get("comments", {}).get("data", [])
            for comment in comments:
                comment_id = comment.get("id")
                if comment_id in self.state["seen_comment_ids"]:
                    continue

                sender = comment.get("from", {})
                if str(sender.get("id")) == str(self.page_id):
                    self.state["seen_comment_ids"].append(comment_id)
                    continue

                items.append({
                    "event_type": "fb_comment",
                    "id": comment_id,
                    "sender_name": sender.get("name", "Unknown"),
                    "sender_id": str(sender.get("id", "")),
                    "text": comment.get("message", ""),
                    "created_time": comment.get("created_time", datetime.now(timezone.utc).isoformat()),
                    "post_id": post.get("id", ""),
                })
                self.state["seen_comment_ids"].append(comment_id)

        if items:
            self.logger.info("Found %d new FB comment(s)", len(items))
        return items

    def _poll_ig_comments(self) -> list[dict]:
        """Fetch recent comments on Instagram posts."""
        data = self._graph_get(
            f"{self.ig_id}/media",
            {"fields": "id,timestamp,comments{id,timestamp,text,username}", "limit": 5},
        )
        items = []
        media_list = data.get("data", [])

        for media in media_list:
            comments = media.get("comments", {}).get("data", [])
            for comment in comments:
                comment_id = comment.get("id")
                if comment_id in self.state["seen_comment_ids"]:
                    continue

                items.append({
                    "event_type": "ig_comment",
                    "id": comment_id,
                    "username": comment.get("username", "unknown"),
                    "text": comment.get("text", ""),
                    "created_time": comment.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "media_id": media.get("id", ""),
                })
                self.state["seen_comment_ids"].append(comment_id)

        if items:
            self.logger.info("Found %d new IG comment(s)", len(items))
        return items

    def _check_follower_counts(self) -> dict | None:
        """Check for significant changes in Page fan count or IG follower count."""
        changes: dict = {}

        # Facebook Page likes/fans
        page_data = self._graph_get(self.page_id, {"fields": "fan_count"})
        fb_count = page_data.get("fan_count", 0)
        fb_prev = self.state.get("last_page_fan_count", 0)
        if abs(fb_count - fb_prev) >= 10:
            changes["facebook"] = {"previous": fb_prev, "current": fb_count, "change": fb_count - fb_prev}
        self.state["last_page_fan_count"] = fb_count

        # Instagram followers
        if self.ig_id:
            ig_data = self._graph_get(self.ig_id, {"fields": "followers_count"})
            ig_count = ig_data.get("followers_count", 0)
            ig_prev = self.state.get("last_ig_follower_count", 0)
            if abs(ig_count - ig_prev) >= 10:
                changes["instagram"] = {"previous": ig_prev, "current": ig_count, "change": ig_count - ig_prev}
            self.state["last_ig_follower_count"] = ig_count

        if changes:
            return {"event_type": "follower_change", "changes": changes, "timestamp": datetime.now(timezone.utc).isoformat()}
        return None

    # ------------------------------------------------------------------
    # File creation
    # ------------------------------------------------------------------

    def create_action_file(self, item: dict) -> Path:
        event_type = item["event_type"]
        if event_type == "fb_message":
            return self._create_fb_message_file(item)
        elif event_type == "fb_comment":
            return self._create_fb_comment_file(item)
        elif event_type == "ig_comment":
            return self._create_ig_comment_file(item)
        elif event_type == "follower_change":
            return self._create_follower_file(item)
        self.logger.warning("Unknown event type: %s", event_type)
        return None

    def _create_fb_message_file(self, item: dict) -> Path:
        uid = hashlib.md5(item["id"].encode()).hexdigest()[:8]
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"FACEBOOK_{date_str}_dm_{uid}.md"
        file_path = self.needs_action / filename

        content = f"""---
type: facebook
event_type: fb_message
platform: facebook
status: pending
created: {datetime.now(timezone.utc).isoformat()}
sender_name: "{item['sender_name']}"
sender_id: "{item['sender_id']}"
logged: false
---

# Facebook Page Message — {item['sender_name']}

**From:** {item['sender_name']}
**Time:** {item['created_time']}

## Message Content

> {item['text']}

## Suggested Action

- If this is a new contact → follow new contact escalation rules
- Draft a reply using `SKILL_Facebook_Instagram` → `Pending_Approval/`
- If it is a complaint or legal matter → `Pending_Approval/` as HUMAN_REVIEW

## Processing Notes

_Add triage notes here._
"""
        file_path.write_text(content, encoding="utf-8")
        log_action("facebook_message_received", "facebook_watcher", item["sender_name"])
        return file_path

    def _create_fb_comment_file(self, item: dict) -> Path:
        uid = hashlib.md5(item["id"].encode()).hexdigest()[:8]
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"FACEBOOK_{date_str}_comment_{uid}.md"
        file_path = self.needs_action / filename

        content = f"""---
type: facebook
event_type: fb_comment
platform: facebook
status: pending
created: {datetime.now(timezone.utc).isoformat()}
sender_name: "{item['sender_name']}"
sender_id: "{item['sender_id']}"
post_id: "{item['post_id']}"
logged: false
---

# Facebook Comment — {item['sender_name']}

**From:** {item['sender_name']}
**Post ID:** {item['post_id']}
**Time:** {item['created_time']}

## Comment Content

> {item['text']}

## Suggested Action

- Positive/question → draft a brief reply via `SKILL_Facebook_Instagram`
- Complaint → `Pending_Approval/` as HUMAN_REVIEW (do NOT auto-reply)
- Generic → LOG_ONLY

## Processing Notes

_Add triage notes here._
"""
        file_path.write_text(content, encoding="utf-8")
        log_action("facebook_comment_received", "facebook_watcher", item["sender_name"])
        return file_path

    def _create_ig_comment_file(self, item: dict) -> Path:
        uid = hashlib.md5(item["id"].encode()).hexdigest()[:8]
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"INSTAGRAM_{date_str}_comment_{uid}.md"
        file_path = self.needs_action / filename

        content = f"""---
type: instagram
event_type: ig_comment
platform: instagram
status: pending
created: {datetime.now(timezone.utc).isoformat()}
username: "@{item['username']}"
media_id: "{item['media_id']}"
logged: false
---

# Instagram Comment — @{item['username']}

**From:** @{item['username']}
**Media ID:** {item['media_id']}
**Time:** {item['created_time']}

## Comment Content

> {item['text']}

## Suggested Action

- Positive/question → draft reply via `SKILL_Facebook_Instagram`
- Complaint → `Pending_Approval/` as HUMAN_REVIEW

## Processing Notes

_Add triage notes here._
"""
        file_path.write_text(content, encoding="utf-8")
        log_action("instagram_comment_received", "facebook_watcher", f"@{item['username']}")
        return file_path

    def _create_follower_file(self, item: dict) -> Path:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"FACEBOOK_{date_str}_followers_{date_str}.md"
        file_path = self.needs_action / filename

        lines = [
            f"---",
            f"type: facebook",
            f"event_type: follower_change",
            f"platform: facebook",
            f"status: pending",
            f"created: {datetime.now(timezone.utc).isoformat()}",
            f"logged: false",
            f"---",
            f"",
            f"# Facebook/Instagram Follower Update",
            f"",
            f"**Time:** {item['timestamp']}",
            f"",
            f"## Changes",
            f"",
        ]
        for platform, data in item["changes"].items():
            direction = "gained" if data["change"] > 0 else "lost"
            lines.append(f"- **{platform.title()}:** {data['previous']} → **{data['current']}** ({data['change']:+d} {direction})")

        lines += [
            f"",
            f"## Action",
            f"Update `Social_Analytics/Facebook_Instagram_Summary.md` with new counts.",
        ]
        file_path.write_text("\n".join(lines), encoding="utf-8")
        log_action("facebook_follower_change", "facebook_watcher", "Social_Analytics/Facebook_Instagram_Summary.md")
        return file_path

    def shutdown(self) -> None:
        _save_state(self.vault_path, self.state)
        self._http.close()
        log_watcher_stop("facebook_watcher")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    from dotenv import load_dotenv

    vault_default = str(Path(__file__).parent)
    parser = argparse.ArgumentParser(description="Facebook/Instagram Watcher for Gold AI Employee")
    parser.add_argument("--vault", default=vault_default)
    parser.add_argument("--interval", type=int, default=int(os.environ.get("FACEBOOK_INTERVAL", 600)))
    args = parser.parse_args()

    load_dotenv(Path(args.vault) / ".env")

    log_watcher_start("facebook_watcher")
    watcher = FacebookWatcher(vault_path=args.vault, check_interval=args.interval)
    watcher.run()


if __name__ == "__main__":
    main()
