"""
linkedin_watcher.py — LinkedIn Watcher for the Platinum-tier AI Employee (Cloud Agent).

Platinum change: writes to Needs_Action/social/ instead of Needs_Action/.
All other logic identical to Gold tier.

Uses Playwright to monitor LinkedIn notifications and inbox.

Usage:
    python linkedin_watcher.py
    python linkedin_watcher.py --vault /path/to/platinum --interval 300
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
except ImportError:
    print("ERROR: playwright not installed. Run: uv run playwright install chromium")
    sys.exit(1)

from base_watcher import BaseWatcher

OPPORTUNITY_KEYWORDS = {
    "collaboration", "partnership", "project", "proposal",
    "interested in your services", "consulting", "freelance",
    "contract", "opportunity", "work together", "hire",
}
URGENT_KEYWORDS = {
    "urgent", "asap", "deadline", "time sensitive", "immediately",
}


class LinkedInWatcher(BaseWatcher):
    """
    Watches LinkedIn notifications and inbox.
    Writes action files to Needs_Action/social/ (Platinum routing).
    """

    SESSION_FILE = ".linkedin_session.json"

    def __init__(
        self,
        vault_path: str = ".",
        check_interval: int = 300,
        headless: bool = True,
        needs_action_subdir: str = "social",   # Platinum: always "social"
    ):
        super().__init__(vault_path, check_interval, needs_action_subdir=needs_action_subdir)
        self.email        = os.getenv("LINKEDIN_EMAIL", "")
        self.password     = os.getenv("LINKEDIN_PASSWORD", "")
        self.headless     = headless
        self.session_path = self.vault_path / self.SESSION_FILE
        self.state_path   = self.vault_path / ".linkedin_watcher_state.json"
        self.processed_ids: set[str] = self._load_state()

        if not self.email or not self.password:
            self.logger.error("LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")
            sys.exit(1)

    def _load_state(self) -> set[str]:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                return set(data.get("processed_ids", []))
            except (json.JSONDecodeError, KeyError):
                pass
        return set()

    def _save_state(self) -> None:
        self.state_path.write_text(
            json.dumps({"processed_ids": sorted(self.processed_ids)}, indent=2),
            encoding="utf-8",
        )

    def check_for_updates(self) -> list:
        self.logger.info("Starting LinkedIn poll via Playwright…")
        notifications = []
        with sync_playwright() as pw:
            browser  = pw.chromium.launch(headless=self.headless)
            context  = self._get_context(browser)
            page     = context.new_page()
            try:
                notifications = self._scrape_notifications(page)
            except PWTimeoutError as e:
                self.logger.error(f"Playwright timeout: {e}")
            except Exception as e:
                self.logger.error(f"LinkedIn poll error: {e}", exc_info=True)
            finally:
                state = context.storage_state()
                self.session_path.write_text(json.dumps(state), encoding="utf-8")
                browser.close()

        new = [n for n in notifications if n.get("id") and n["id"] not in self.processed_ids]
        self.logger.info(f"LinkedIn poll: {len(notifications)} total, {len(new)} new")
        return new

    def _get_context(self, browser):
        if self.session_path.exists():
            try:
                saved = json.loads(self.session_path.read_text(encoding="utf-8"))
                return browser.new_context(storage_state=saved)
            except Exception:
                self.logger.warning("Saved LinkedIn session invalid, logging in fresh")
        context = browser.new_context()
        page    = context.new_page()
        if not self._login(page):
            raise RuntimeError("LinkedIn login failed")
        return context

    def _login(self, page) -> bool:
        self.logger.info("Logging into LinkedIn…")
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        page.fill("#username", self.email)
        page.fill("#password", self.password)
        page.click('[type="submit"]')
        try:
            page.wait_for_url(
                re.compile(r"linkedin\.com/(feed|home|checkpoint|mynetwork)"),
                timeout=45_000,
            )
            if "checkpoint" in page.url:
                self.logger.warning("LinkedIn checkpoint detected — waiting 60s for manual completion")
                try:
                    page.wait_for_url(re.compile(r"linkedin\.com/feed"), timeout=60_000)
                except PWTimeoutError:
                    self.logger.error("Checkpoint not completed — will retry next poll")
                    return False
            self.logger.info("LinkedIn login successful")
            return True
        except PWTimeoutError:
            self.logger.error("LinkedIn login timed out")
            return False

    def _scrape_notifications(self, page) -> list:
        page.goto("https://www.linkedin.com/notifications/", wait_until="domcontentloaded")
        try:
            page.wait_for_selector(".nt-card-list, .notification-card, [data-urn]", timeout=10_000)
        except PWTimeoutError:
            self.logger.warning("Notification list not found")
            return []

        notifications = []
        cards = page.query_selector_all(".nt-card-list .nt-card, .notification-card")
        for i, card in enumerate(cards[:20]):
            try:
                text     = card.inner_text().strip()
                raw_urn  = card.get_attribute("data-urn") or ""
                urn      = raw_urn or hashlib.sha256(f"notif:{i}:{text[:120]}".encode()).hexdigest()[:16]
                link_el  = card.query_selector("a")
                link     = link_el.get_attribute("href") if link_el else ""
                category = self._categorise(text)
                priority = self._detect_priority(text)
                notifications.append({"id": urn, "text": text[:1000], "link": link,
                                       "category": category, "priority": priority})
            except Exception as e:
                self.logger.warning(f"Error scraping notification {i}: {e}")

        notifications.extend(self._scrape_inbox(page))
        return notifications

    def _scrape_inbox(self, page) -> list:
        try:
            page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded")
            page.wait_for_selector(".msg-conversation-card, .msg-overlay-list-bubble", timeout=8_000)
        except PWTimeoutError:
            return []
        messages = []
        cards = page.query_selector_all(
            ".msg-conversation-card--unread, .msg-conversation-card[aria-label*='unread']"
        )
        for i, card in enumerate(cards[:10]):
            try:
                text    = card.inner_text().strip()
                raw_urn = card.get_attribute("data-entity-urn") or ""
                urn     = raw_urn or hashlib.sha256(f"msg:{i}:{text[:120]}".encode()).hexdigest()[:16]
                messages.append({
                    "id": urn, "text": text[:800],
                    "link": "https://www.linkedin.com/messaging/",
                    "category": "inbox_message",
                    "priority": self._detect_priority(text),
                })
            except Exception as e:
                self.logger.warning(f"Error scraping inbox card {i}: {e}")
        return messages

    def _categorise(self, text: str) -> str:
        lower = text.lower()
        if any(kw in lower for kw in OPPORTUNITY_KEYWORDS):
            return "business_opportunity"
        if "connection" in lower or "connect" in lower:
            return "connection_request"
        if "mentioned" in lower or "comment" in lower:
            return "mention_or_comment"
        if "liked" in lower or "reacted" in lower:
            return "engagement"
        return "general_notification"

    def _detect_priority(self, text: str) -> str:
        lower = text.lower()
        if any(kw in lower for kw in URGENT_KEYWORDS):
            return "urgent"
        if any(kw in lower for kw in OPPORTUNITY_KEYWORDS):
            return "high"
        if "connection" in lower:
            return "medium"
        return "low"

    # ------------------------------------------------------------------
    # File creation — writes to Needs_Action/social/
    # ------------------------------------------------------------------

    def create_action_file(self, notification: dict) -> Path | None:
        ACTIONABLE = {"business_opportunity", "connection_request", "inbox_message", "mention_or_comment"}
        category   = notification["category"]

        if category not in ACTIONABLE:
            self.processed_ids.add(notification["id"])
            self._save_state()
            return None

        date_slug = datetime.now().strftime("%Y-%m-%d")
        text_slug = self._slugify(notification["text"], max_len=40)
        uniq      = hashlib.sha256(f"{notification['id']}|{notification['text']}".encode()).hexdigest()[:8]
        filename  = f"LINKEDIN_{date_slug}_{text_slug}_{uniq}.md"
        filepath  = self.needs_action / filename  # → Needs_Action/social/

        received_iso      = datetime.now(timezone.utc).isoformat()
        draft_suggestion  = ""
        if category == "business_opportunity":
            draft_suggestion = "- [ ] Use SKILL_LinkedIn_Draft to draft a response post"

        content = f"""\
---
type: linkedin_opportunity
agent_target: cloud_agent
linkedin_id: "{notification['id']}"
category: {category}
link: "{notification.get('link', '')}"
received: "{received_iso}"
priority: {notification['priority']}
status: pending
source: linkedin
---

# LinkedIn: {category.replace('_', ' ').title()}

**Category:** {category}
**Priority:** {notification['priority']}
**Link:** {notification.get('link', 'N/A')}
**Received:** {received_iso}

---

## Notification Content

{notification['text']}

---

## Suggested Actions

- [ ] Review this LinkedIn notification
- [ ] Reply via LinkedIn (use HITL if new contact → Pending_Approval/social/)
{draft_suggestion}
- [ ] Log as business intelligence

---

## Processing Notes

> _(Cloud Agent: add analysis and action taken here)_

---

*Captured by LinkedInWatcher (Platinum/Cloud) at {received_iso}*
"""
        try:
            filepath.write_text(content, encoding="utf-8")
        except OSError as e:
            self.logger.error(f"Failed to write file {filename}: {e}")
            return None

        self.processed_ids.add(notification["id"])
        self._save_state()
        self.logger.info(f"Created: {filename} | Category: {category}")
        return filepath

    @staticmethod
    def _slugify(text: str, max_len: int = 40) -> str:
        slug = re.sub(r"[^\w\s-]", "", text).strip()
        slug = re.sub(r"[\s_]+", "_", slug)
        return slug[:max_len].strip("_") or "notification"

    def shutdown(self) -> None:
        self.logger.info("LinkedInWatcher stopped.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LinkedInWatcher — Platinum Cloud Agent")
    parser.add_argument("--vault",       default=".")
    parser.add_argument("--interval",    type=int, default=300)
    parser.add_argument("--no-headless", action="store_true")
    args = parser.parse_args()
    load_dotenv(Path(args.vault) / ".env")
    LinkedInWatcher(
        vault_path=args.vault,
        check_interval=args.interval,
        headless=not args.no_headless,
        needs_action_subdir="social",
    ).run()
