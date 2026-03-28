"""
twitter_watcher.py — Twitter/X Watcher for the Platinum-tier AI Employee (Cloud Agent).

Platinum change: writes to Needs_Action/social/ instead of Needs_Action/.
All other logic identical to Gold tier.

Polls Twitter/X for mentions, DMs, and follower changes.
State is persisted in .twitter_watcher_state.json.

Usage:
    python twitter_watcher.py
    python twitter_watcher.py --vault /path/to/platinum --interval 300
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import tweepy
from dotenv import load_dotenv

from base_watcher import BaseWatcher
from audit_logger import log_action, log_watcher_start, log_watcher_stop, log_error

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
    (vault_path / STATE_FILE_NAME).write_text(json.dumps(state, indent=2), encoding="utf-8")


class TwitterWatcher(BaseWatcher):
    """
    Watches Twitter/X API v2 for mentions, DMs, and follower changes.
    Writes action files to Needs_Action/social/ (Platinum routing).
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 300,
        needs_action_subdir: str = "social",   # Platinum: always "social"
    ):
        super().__init__(vault_path, check_interval, needs_action_subdir=needs_action_subdir)
        self.state    = _load_state(self.vault_path)
        self._client: tweepy.Client | None = None
        self._me:     tweepy.User   | None = None
        self._setup_client()

    def _setup_client(self) -> None:
        bearer  = os.environ.get("TWITTER_BEARER_TOKEN")
        api_key = os.environ.get("TWITTER_API_KEY")
        api_sec = os.environ.get("TWITTER_API_SECRET")
        acc_tok = os.environ.get("TWITTER_ACCESS_TOKEN")
        acc_sec = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

        if not all([bearer, api_key, api_sec, acc_tok, acc_sec]):
            self.logger.error(
                "Missing Twitter credentials. Set TWITTER_BEARER_TOKEN, "
                "TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, "
                "TWITTER_ACCESS_TOKEN_SECRET in .env"
            )
            sys.exit(1)

        self._client = tweepy.Client(
            bearer_token=bearer,
            consumer_key=api_key, consumer_secret=api_sec,
            access_token=acc_tok, access_token_secret=acc_sec,
            wait_on_rate_limit=True,
        )
        try:
            me_resp  = self._client.get_me(user_fields=["public_metrics"])
            self._me = me_resp.data
            self.logger.info("Authenticated as @%s (id=%s)", self._me.username, self._me.id)
        except tweepy.TweepyException as exc:
            self.logger.error("Twitter auth failed: %s", exc)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Poll
    # ------------------------------------------------------------------

    def check_for_updates(self) -> list[dict]:
        items: list[dict] = []
        try:
            items.extend(self._poll_mentions())
        except tweepy.TweepyException as exc:
            self.logger.warning("Mentions poll failed: %s", exc)
            log_error("twitter_watcher", "mentions_poll", str(exc))
        try:
            items.extend(self._poll_dms())
        except tweepy.TweepyException as exc:
            self.logger.warning("DM poll failed: %s", exc)
            log_error("twitter_watcher", "dm_poll", str(exc))
        try:
            follower_item = self._check_follower_count()
            if follower_item:
                items.append(follower_item)
        except tweepy.TweepyException as exc:
            self.logger.warning("Follower check failed: %s", exc)
        _save_state(self.vault_path, self.state)
        return items

    def _poll_mentions(self) -> list[dict]:
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
        users = {u.id: u for u in (resp.includes.get("users") or [])}
        items = []
        for tweet in resp.data:
            author = users.get(tweet.author_id)
            items.append({
                "event_type":       "mention",
                "tweet_id":         str(tweet.id),
                "author_id":        str(tweet.author_id),
                "author_username":  author.username if author else "unknown",
                "author_name":      author.name if author else "Unknown",
                "text":             tweet.text,
                "created_at":       tweet.created_at.isoformat() if tweet.created_at else datetime.now(timezone.utc).isoformat(),
                "conversation_id":  str(tweet.conversation_id) if tweet.conversation_id else None,
            })
        self.state["last_mention_id"] = str(resp.data[0].id)
        self.logger.info("Found %d new mention(s)", len(items))
        return items

    def _poll_dms(self) -> list[dict]:
        kwargs: dict = {"dm_event_fields": ["created_at", "text", "sender_id"], "max_results": 10}
        if self.state["last_dm_id"]:
            kwargs["since_id"] = self.state["last_dm_id"]
        try:
            resp = self._client.get_direct_message_events(**kwargs)
        except tweepy.errors.Forbidden:
            return []
        if not resp.data:
            return []
        items = []
        for dm in resp.data:
            if str(dm.sender_id) == str(self._me.id):
                continue
            items.append({
                "event_type": "dm",
                "dm_id":      str(dm.id),
                "sender_id":  str(dm.sender_id),
                "text":       dm.text,
                "created_at": dm.created_at.isoformat() if dm.created_at else datetime.now(timezone.utc).isoformat(),
            })
        if resp.data:
            self.state["last_dm_id"] = str(resp.data[0].id)
        self.logger.info("Found %d new DM(s)", len(items))
        return items

    def _check_follower_count(self) -> dict | None:
        resp = self._client.get_user(id=self._me.id, user_fields=["public_metrics"])
        if not resp.data or not resp.data.public_metrics:
            return None
        current  = resp.data.public_metrics.get("followers_count", 0)
        previous = self.state.get("last_follower_count", 0)
        change   = current - previous
        self.state["last_follower_count"] = current
        if abs(change) >= 10:
            self.logger.info("Follower count changed: %d → %d (%+d)", previous, current, change)
            return {
                "event_type": "follower_change",
                "previous":   previous,
                "current":    current,
                "change":     change,
                "timestamp":  datetime.now(timezone.utc).isoformat(),
            }
        return None

    # ------------------------------------------------------------------
    # File creation — writes to Needs_Action/social/
    # ------------------------------------------------------------------

    def create_action_file(self, item: dict) -> Path:
        event_type = item["event_type"]
        if event_type == "mention":
            return self._create_mention_file(item)
        elif event_type == "dm":
            return self._create_dm_file(item)
        elif event_type == "follower_change":
            return self._create_follower_file(item)
        self.logger.warning("Unknown event type: %s", event_type)
        return None

    def _create_mention_file(self, item: dict) -> Path:
        uid       = hashlib.md5(item["tweet_id"].encode()).hexdigest()[:8]
        date_str  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename  = f"TWITTER_{date_str}_mention_{uid}.md"
        file_path = self.needs_action / filename  # → Needs_Action/social/

        content = f"""---
type: twitter
event_type: mention
platform: twitter
agent_target: cloud_agent
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

- 🟡 **Reply** — Draft reply via `SKILL_Twitter_Draft` → `Pending_Approval/social/`
- 🔴 **Escalate** — If complaint/sensitive → `Pending_Approval/social/` as HUMAN_REVIEW
- 🟢 **Log only** — Generic mention, no response needed

## Processing Notes

_(Cloud Agent: add triage notes and move to Done/ when complete)_
"""
        file_path.write_text(content, encoding="utf-8")
        log_action("twitter_mention_received", "twitter_watcher",
                   f"@{item['author_username']}", notes=f"Tweet ID {item['tweet_id']}")
        return file_path

    def _create_dm_file(self, item: dict) -> Path:
        uid       = hashlib.md5(item["dm_id"].encode()).hexdigest()[:8]
        date_str  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename  = f"TWITTER_{date_str}_dm_{uid}.md"
        file_path = self.needs_action / filename

        content = f"""---
type: twitter
event_type: dm
platform: twitter
agent_target: cloud_agent
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

- Draft reply via `SKILL_Twitter_Draft` → `Pending_Approval/social/`
- New contact? Follow new contact escalation rules from `Company_Handbook.md`

## Processing Notes

_(Cloud Agent: add triage notes)_
"""
        file_path.write_text(content, encoding="utf-8")
        log_action("twitter_dm_received", "twitter_watcher",
                   f"sender:{item['sender_id']}", notes=f"DM ID {item['dm_id']}")
        return file_path

    def _create_follower_file(self, item: dict) -> Path:
        date_str  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename  = f"TWITTER_{date_str}_followers_{date_str}.md"
        file_path = self.needs_action / filename
        direction = "gained" if item["change"] > 0 else "lost"

        content = f"""---
type: twitter
event_type: follower_change
platform: twitter
agent_target: cloud_agent
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

## Action

Update Social_Analytics if maintained. If +50 or more, consider a thank-you tweet draft.
"""
        file_path.write_text(content, encoding="utf-8")
        log_action("twitter_follower_change", "twitter_watcher",
                   notes=f"Followers: {item['previous']} → {item['current']}")
        return file_path

    def shutdown(self) -> None:
        _save_state(self.vault_path, self.state)
        log_watcher_stop("twitter_watcher")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TwitterWatcher — Platinum Cloud Agent")
    parser.add_argument("--vault",    default=str(Path(__file__).parent))
    parser.add_argument("--interval", type=int,
                        default=int(os.environ.get("TWITTER_INTERVAL", 300)))
    args = parser.parse_args()
    load_dotenv(Path(args.vault) / ".env")
    log_watcher_start("twitter_watcher")
    TwitterWatcher(vault_path=args.vault, check_interval=args.interval,
                   needs_action_subdir="social").run()
