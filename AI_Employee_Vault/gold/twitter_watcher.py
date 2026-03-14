"""
twitter_watcher.py — Twitter/X Watcher for the Gold-tier AI Employee.

Polls Twitter/X for:
  - New mentions of the authenticated user
  - New direct messages
  - Follower count changes (for Social_Analytics)

Creates structured .md files in Needs_Action/ for Claude to process.
Uses Tweepy with Twitter API v2 (Basic tier or higher required).

State is persisted in .twitter_watcher_state.json to avoid duplicate files.

Usage:
    python twitter_watcher.py
    python twitter_watcher.py --vault /path/to/gold --interval 300

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

import tweepy

from base_watcher import BaseWatcher
from audit_logger import log_action, log_watcher_start, log_watcher_stop, log_error

# ---------------------------------------------------------------------------
# State file — tracks last-seen IDs so we never duplicate
# ---------------------------------------------------------------------------
STATE_FILE_NAME = ".twitter_watcher_state.json"


def _load_state(vault_path: Path) -> dict:
    state_file = vault_path / STATE_FILE_NAME
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_mention_id": None, "last_dm_id": None, "last_follower_count": 0}


def _save_state(vault_path: Path, state: dict) -> None:
    state_file = vault_path / STATE_FILE_NAME
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Watcher class
# ---------------------------------------------------------------------------

class TwitterWatcher(BaseWatcher):
    """Polls Twitter/X API v2 for mentions, DMs, and follower changes."""

    def __init__(self, vault_path: str, check_interval: int = 300):
        super().__init__(vault_path, check_interval)
        self.state = _load_state(self.vault_path)
        self._client: tweepy.Client | None = None
        self._me: tweepy.User | None = None
        self._setup_client()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _setup_client(self) -> None:
        """Initialise Tweepy client from environment variables."""
        bearer  = os.environ.get("TWITTER_BEARER_TOKEN")
        api_key = os.environ.get("TWITTER_API_KEY")
        api_sec = os.environ.get("TWITTER_API_SECRET")
        acc_tok = os.environ.get("TWITTER_ACCESS_TOKEN")
        acc_sec = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

        if not all([bearer, api_key, api_sec, acc_tok, acc_sec]):
            self.logger.error(
                "Missing Twitter credentials in environment. "
                "Set TWITTER_BEARER_TOKEN, TWITTER_API_KEY, TWITTER_API_SECRET, "
                "TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET in .env"
            )
            sys.exit(1)

        self._client = tweepy.Client(
            bearer_token=bearer,
            consumer_key=api_key,
            consumer_secret=api_sec,
            access_token=acc_tok,
            access_token_secret=acc_sec,
            wait_on_rate_limit=True,
        )

        try:
            me_resp = self._client.get_me(user_fields=["public_metrics"])
            self._me = me_resp.data
            self.logger.info(
                "Authenticated as @%s (id=%s)", self._me.username, self._me.id
            )
        except tweepy.TweepyException as exc:
            self.logger.error("Twitter auth failed: %s", exc)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Poll
    # ------------------------------------------------------------------

    def check_for_updates(self) -> list[dict]:
        """Poll Twitter for new mentions, DMs, and follower changes."""
        items: list[dict] = []

        # Mentions
        try:
            items.extend(self._poll_mentions())
        except tweepy.TweepyException as exc:
            self.logger.warning("Mentions poll failed: %s", exc)
            log_error("twitter_watcher", "mentions_poll", str(exc))

        # DMs
        try:
            items.extend(self._poll_dms())
        except tweepy.TweepyException as exc:
            self.logger.warning("DM poll failed: %s", exc)
            log_error("twitter_watcher", "dm_poll", str(exc))

        # Follower count change
        try:
            follower_item = self._check_follower_count()
            if follower_item:
                items.append(follower_item)
        except tweepy.TweepyException as exc:
            self.logger.warning("Follower check failed: %s", exc)

        _save_state(self.vault_path, self.state)
        return items

    def _poll_mentions(self) -> list[dict]:
        """Fetch new mentions since last seen ID."""
        kwargs: dict = {
            "id": self._me.id,
            "tweet_fields": ["created_at", "text", "author_id", "conversation_id"],
            "expansions": ["author_id"],
            "user_fields": ["username", "name"],
            "max_results": 10,
        }
        if self.state["last_mention_id"]:
            kwargs["since_id"] = self.state["last_mention_id"]

        resp = self._client.get_users_mentions(**kwargs)
        if not resp.data:
            return []

        # Build author lookup
        users = {u.id: u for u in (resp.includes.get("users") or [])}

        items = []
        for tweet in resp.data:
            author = users.get(tweet.author_id)
            items.append({
                "event_type": "mention",
                "tweet_id": str(tweet.id),
                "author_id": str(tweet.author_id),
                "author_username": author.username if author else "unknown",
                "author_name": author.name if author else "Unknown",
                "text": tweet.text,
                "created_at": tweet.created_at.isoformat() if tweet.created_at else datetime.now(timezone.utc).isoformat(),
                "conversation_id": str(tweet.conversation_id) if tweet.conversation_id else None,
            })

        # Track newest
        self.state["last_mention_id"] = str(resp.data[0].id)
        self.logger.info("Found %d new mention(s)", len(items))
        return items

    def _poll_dms(self) -> list[dict]:
        """Fetch new direct messages."""
        kwargs: dict = {"dm_event_fields": ["created_at", "text", "sender_id"], "max_results": 10}
        if self.state["last_dm_id"]:
            kwargs["since_id"] = self.state["last_dm_id"]

        try:
            resp = self._client.get_direct_message_events(**kwargs)
        except tweepy.errors.Forbidden:
            # DM access requires Elevated API access — skip silently
            return []

        if not resp.data:
            return []

        items = []
        for dm in resp.data:
            if str(dm.sender_id) == str(self._me.id):
                continue  # Skip our own outbound DMs
            items.append({
                "event_type": "dm",
                "dm_id": str(dm.id),
                "sender_id": str(dm.sender_id),
                "text": dm.text,
                "created_at": dm.created_at.isoformat() if dm.created_at else datetime.now(timezone.utc).isoformat(),
            })

        if resp.data:
            self.state["last_dm_id"] = str(resp.data[0].id)

        self.logger.info("Found %d new DM(s)", len(items))
        return items

    def _check_follower_count(self) -> dict | None:
        """Check for significant follower count change (±10 or more)."""
        resp = self._client.get_user(
            id=self._me.id, user_fields=["public_metrics"]
        )
        if not resp.data or not resp.data.public_metrics:
            return None

        current = resp.data.public_metrics.get("followers_count", 0)
        previous = self.state.get("last_follower_count", 0)
        change = current - previous

        # Update state always
        self.state["last_follower_count"] = current

        # Only create an action file if change is ≥ 10 (avoid noise)
        if abs(change) >= 10:
            self.logger.info(
                "Follower count changed: %d → %d (%+d)", previous, current, change
            )
            return {
                "event_type": "follower_change",
                "previous": previous,
                "current": current,
                "change": change,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return None

    # ------------------------------------------------------------------
    # File creation
    # ------------------------------------------------------------------

    def create_action_file(self, item: dict) -> Path:
        """Write a Needs_Action/ .md file for a Twitter event."""
        event_type = item["event_type"]

        if event_type == "mention":
            return self._create_mention_file(item)
        elif event_type == "dm":
            return self._create_dm_file(item)
        elif event_type == "follower_change":
            return self._create_follower_file(item)
        else:
            self.logger.warning("Unknown event type: %s", event_type)
            return None

    def _create_mention_file(self, item: dict) -> Path:
        uid = hashlib.md5(item["tweet_id"].encode()).hexdigest()[:8]
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"TWITTER_{date_str}_mention_{uid}.md"
        file_path = self.needs_action / filename

        content = f"""---
type: twitter
event_type: mention
platform: twitter
status: pending
created: {datetime.now(timezone.utc).isoformat()}
tweet_id: "{item['tweet_id']}"
author_username: "@{item['author_username']}"
author_name: "{item['author_name']}"
conversation_id: "{item.get('conversation_id', '')}"
logged: false
---

# Twitter Mention — @{item['author_username']}

**From:** {item['author_name']} (@{item['author_username']})
**Tweet ID:** {item['tweet_id']}
**Time:** {item['created_at']}

## Tweet Content

> {item['text']}

## Suggested Action

- 🟡 **Reply** — If this is a question or positive engagement, use `SKILL_Twitter_Draft` to draft a reply
- 🔴 **Escalate** — If this is a complaint or sensitive matter, move to `Pending_Approval/` for human review
- 🟢 **Log only** — If this is a generic mention that doesn't need a response

## Processing Notes

_Add triage notes here after review._
"""
        file_path.write_text(content, encoding="utf-8")
        log_action(
            action_type="twitter_mention_received",
            source="twitter_watcher",
            target=f"@{item['author_username']}",
            approval_status="not_required",
            notes=f"Tweet ID {item['tweet_id']}",
        )
        return file_path

    def _create_dm_file(self, item: dict) -> Path:
        uid = hashlib.md5(item["dm_id"].encode()).hexdigest()[:8]
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"TWITTER_{date_str}_dm_{uid}.md"
        file_path = self.needs_action / filename

        content = f"""---
type: twitter
event_type: dm
platform: twitter
status: pending
created: {datetime.now(timezone.utc).isoformat()}
dm_id: "{item['dm_id']}"
sender_id: "{item['sender_id']}"
logged: false
---

# Twitter DM — Sender ID {item['sender_id']}

**Sender ID:** {item['sender_id']}
**Time:** {item['created_at']}

## Message Content

> {item['text']}

## Suggested Action

- Draft a reply using `SKILL_Twitter_Draft`
- If from a new contact — follow new contact escalation rules from `Company_Handbook.md`

## Processing Notes

_Add triage notes here after review._
"""
        file_path.write_text(content, encoding="utf-8")
        log_action(
            action_type="twitter_dm_received",
            source="twitter_watcher",
            target=f"sender:{item['sender_id']}",
            approval_status="not_required",
            notes=f"DM ID {item['dm_id']}",
        )
        return file_path

    def _create_follower_file(self, item: dict) -> Path:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"TWITTER_{date_str}_followers_{date_str}.md"
        file_path = self.needs_action / filename

        direction = "gained" if item["change"] > 0 else "lost"
        content = f"""---
type: twitter
event_type: follower_change
platform: twitter
status: pending
created: {datetime.now(timezone.utc).isoformat()}
previous_count: {item['previous']}
current_count: {item['current']}
change: {item['change']:+d}
logged: false
---

# Twitter Follower Update

**Followers:** {item['previous']} → **{item['current']}** ({item['change']:+d} {direction})
**Time:** {item['timestamp']}

## Action Required

Update `Social_Analytics/Twitter_Summary.md` with the new follower count.

If significant growth (+50 or more), consider:
- Drafting a thank-you tweet via `SKILL_Twitter_Draft`
- Noting in the next CEO Briefing
"""
        file_path.write_text(content, encoding="utf-8")
        log_action(
            action_type="twitter_follower_change",
            source="twitter_watcher",
            target="Social_Analytics/Twitter_Summary.md",
            notes=f"Followers: {item['previous']} → {item['current']} ({item['change']:+d})",
        )
        return file_path

    def shutdown(self) -> None:
        _save_state(self.vault_path, self.state)
        log_watcher_stop("twitter_watcher")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    from dotenv import load_dotenv

    vault_default = str(Path(__file__).parent)
    parser = argparse.ArgumentParser(description="Twitter Watcher for Gold AI Employee")
    parser.add_argument("--vault", default=vault_default)
    parser.add_argument("--interval", type=int, default=int(os.environ.get("TWITTER_INTERVAL", 300)))
    args = parser.parse_args()

    load_dotenv(Path(args.vault) / ".env")

    log_watcher_start("twitter_watcher")
    watcher = TwitterWatcher(vault_path=args.vault, check_interval=args.interval)
    watcher.run()


if __name__ == "__main__":
    main()
