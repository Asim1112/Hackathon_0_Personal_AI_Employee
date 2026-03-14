"""
linkedin_watcher.py — LinkedIn Watcher for the Silver-tier AI Employee.

Uses Playwright to monitor LinkedIn notifications for:
- New connection requests (potential new business contacts)
- Messages in LinkedIn inbox
- Mentions or comments on company posts
- Job-related signals that may be business opportunities

Creates structured .md files in Needs_Action/ for each actionable notification.
Typically started by scheduler.py at 8 AM daily.

Architecture: Playwright → LinkedIn → Needs_Action/ → Claude → Done/ or Pending_Approval/

Usage:
    python linkedin_watcher.py
    python linkedin_watcher.py --vault /path/to/silver --interval 300

    Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env (or environment).
    Set HEADLESS=false to see the browser window (useful for first login / CAPTCHA).

Dependencies (install via uv):
    uv sync  (includes playwright)
    uv run playwright install chromium  (one-time browser install)
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load .env from vault root
load_dotenv(Path(__file__).parent / ".env")

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
except ImportError:
    print("ERROR: playwright not installed. Run: uv run playwright install chromium")
    sys.exit(1)

from base_watcher import BaseWatcher


# ---------------------------------------------------------------------------
# Notification categories that signal business opportunities
# ---------------------------------------------------------------------------

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
    Watches LinkedIn notifications and inbox for business-relevant signals.

    Uses Playwright browser automation to log in and scrape notifications.
    Writes actionable items as .md files to Needs_Action/.

    Args:
        vault_path:     Root of the Silver vault.
        check_interval: Seconds between LinkedIn polls. Default 300.
        headless:       Run browser in headless mode. Default True.
    """

    SESSION_FILE = ".linkedin_session.json"

    def __init__(
        self,
        vault_path: str = ".",
        check_interval: int = 300,
        headless: bool = True,
    ):
        super().__init__(vault_path, check_interval)

        self.email    = os.getenv("LINKEDIN_EMAIL", "")
        self.password = os.getenv("LINKEDIN_PASSWORD", "")
        self.headless = headless

        self.session_path = self.vault_path / self.SESSION_FILE
        self.state_path   = self.vault_path / ".linkedin_watcher_state.json"
        self.processed_ids: set[str] = self._load_state()

        if not self.email or not self.password:
            self.logger.error(
                "LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env"
            )
            sys.exit(1)

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _load_state(self) -> set[str]:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                ids = set(data.get("processed_ids", []))
                self.logger.info(f"Loaded {len(ids)} processed LinkedIn notification IDs")
                return ids
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"Could not read LinkedIn state file ({e})")
        return set()

    def _save_state(self) -> None:
        self.state_path.write_text(
            json.dumps({"processed_ids": sorted(self.processed_ids)}, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # BaseWatcher interface — check_for_updates
    # ------------------------------------------------------------------

    def check_for_updates(self) -> list:
        """
        Launch Playwright, log into LinkedIn, and scrape recent notifications.
        Returns a list of notification dicts for unseen items.
        """
        self.logger.info("Starting LinkedIn poll via Playwright...")
        notifications = []

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless)
            context = self._get_context(browser)
            page = context.new_page()

            try:
                notifications = self._scrape_notifications(page)
            except PWTimeoutError as e:
                self.logger.error(f"Playwright timeout during LinkedIn poll: {e}")
            except Exception as e:
                self.logger.error(f"LinkedIn poll error: {e}", exc_info=True)
            finally:
                # Save updated session state
                state = context.storage_state()
                self.session_path.write_text(
                    json.dumps(state), encoding="utf-8"
                )
                browser.close()

        new_notifications = [
            n for n in notifications
            if n.get("id") and n["id"] not in self.processed_ids
        ]
        self.logger.info(
            f"LinkedIn poll: {len(notifications)} notifications, "
            f"{len(new_notifications)} new"
        )
        return new_notifications

    def _get_context(self, browser):
        """Return a browser context, restoring saved session if available."""
        if self.session_path.exists():
            try:
                saved = json.loads(self.session_path.read_text(encoding="utf-8"))
                return browser.new_context(storage_state=saved)
            except Exception:
                self.logger.warning("Saved LinkedIn session invalid, logging in fresh")

        context = browser.new_context()
        page = context.new_page()
        ok = self._login(page)
        if not ok:
            raise RuntimeError("LinkedIn login failed — see log above")
        return context

    def _login(self, page) -> bool:
        """
        Log into LinkedIn. Returns True on success, False on failure.
        Does NOT exit the process — caller decides whether to retry.
        """
        self.logger.info("Logging into LinkedIn...")
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        page.fill("#username", self.email)
        page.fill("#password", self.password)
        page.click('[type="submit"]')
        try:
            # LinkedIn may redirect to /feed, /checkpoint/challenge, or /home
            page.wait_for_url(
                re.compile(r"linkedin\.com/(feed|home|checkpoint|mynetwork)"),
                timeout=45_000,
            )
            if "checkpoint" in page.url:
                self.logger.warning(
                    "LinkedIn checkpoint/CAPTCHA page detected. "
                    "Complete it in the browser window, then wait..."
                )
                # Give the user up to 60s to complete the challenge
                try:
                    page.wait_for_url(re.compile(r"linkedin\.com/feed"), timeout=60_000)
                except PWTimeoutError:
                    self.logger.error("Checkpoint not completed in time — will retry next poll")
                    return False
            self.logger.info("LinkedIn login successful")
            return True
        except PWTimeoutError:
            self.logger.error(
                "LinkedIn login timed out. "
                "Run with --no-headless to complete any verification manually."
            )
            return False

    def _scrape_notifications(self, page) -> list:
        """
        Navigate to LinkedIn notifications page and extract recent items.
        Returns a list of dicts with notification data.
        """
        page.goto("https://www.linkedin.com/notifications/", wait_until="domcontentloaded")

        try:
            page.wait_for_selector(
                ".nt-card-list, .notification-card, [data-urn]",
                timeout=10_000
            )
        except PWTimeoutError:
            self.logger.warning("Notification list not found — LinkedIn layout may have changed")
            return []

        # Scrape notification cards
        notifications = []
        cards = page.query_selector_all(".nt-card-list .nt-card, .notification-card")

        for i, card in enumerate(cards[:20]):  # limit to 20 most recent
            try:
                text     = card.inner_text().strip()
                # Stable fallback ID: hash of position + first 120 chars of text.
                # Never use time-based values — they change every poll and break dedup.
                raw_urn  = card.get_attribute("data-urn") or ""
                urn      = raw_urn or hashlib.sha256(f"notif:{i}:{text[:120]}".encode()).hexdigest()[:16]
                link_el  = card.query_selector("a")
                link     = link_el.get_attribute("href") if link_el else ""

                category = self._categorise(text)
                priority = self._detect_priority(text)

                notifications.append({
                    "id":       urn,
                    "text":     text[:1000],
                    "link":     link,
                    "category": category,
                    "priority": priority,
                })
            except Exception as e:
                self.logger.warning(f"Error scraping notification {i}: {e}")

        # Also check LinkedIn inbox for new messages
        inbox_items = self._scrape_inbox(page)
        notifications.extend(inbox_items)

        return notifications

    def _scrape_inbox(self, page) -> list:
        """Scrape unread messages from LinkedIn inbox."""
        try:
            page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded")
            page.wait_for_selector(".msg-conversation-card, .msg-overlay-list-bubble", timeout=8_000)
        except PWTimeoutError:
            return []

        messages = []
        cards = page.query_selector_all(".msg-conversation-card--unread, .msg-conversation-card[aria-label*='unread']")

        for i, card in enumerate(cards[:10]):
            try:
                text    = card.inner_text().strip()
                raw_urn = card.get_attribute("data-entity-urn") or ""
                urn     = raw_urn or hashlib.sha256(f"msg:{i}:{text[:120]}".encode()).hexdigest()[:16]
                messages.append({
                    "id":       urn,
                    "text":     text[:800],
                    "link":     "https://www.linkedin.com/messaging/",
                    "category": "inbox_message",
                    "priority": self._detect_priority(text),
                })
            except Exception as e:
                self.logger.warning(f"Error scraping inbox card {i}: {e}")

        return messages

    def _categorise(self, text: str) -> str:
        """Classify a notification text into a business category."""
        lower = text.lower()
        if any(kw in lower for kw in OPPORTUNITY_KEYWORDS):
            return "business_opportunity"
        if "connection" in lower or "connect" in lower:
            return "connection_request"
        if "mentioned" in lower or "comment" in lower:
            return "mention_or_comment"
        if "liked" in lower or "reacted" in lower:
            return "engagement"
        if "job" in lower or "hiring" in lower:
            return "job_signal"
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
    # BaseWatcher interface — create_action_file
    # ------------------------------------------------------------------

    def create_action_file(self, notification: dict) -> Path | None:
        """Write a structured .md file to Needs_Action/ for the notification."""
        notif_id  = notification["id"]
        category  = notification["category"]
        priority  = notification["priority"]
        text      = notification["text"]
        link      = notification.get("link", "")

        # Only write files for categories worth Claude's attention.
        # Everything else is marked processed and silently discarded.
        ACTIONABLE_CATEGORIES = {
            "business_opportunity",  # opportunity keywords detected
            "connection_request",    # new potential contact
            "inbox_message",         # someone DM'd
            "mention_or_comment",    # someone engaged with your content
        }
        if category not in ACTIONABLE_CATEGORIES:
            self.logger.info(
                f"Skipping '{category}' notification (low value): "
                f"{text[:60].strip()!r}"
            )
            self.processed_ids.add(notif_id)
            self._save_state()
            return None

        date_slug    = datetime.now().strftime("%Y-%m-%d")
        text_slug    = self._slugify(text, max_len=40)
        # Use a hash of (id + text) so duplicate notification texts never
        # produce the same filename, even when data-urn is unavailable.
        uniq = hashlib.sha256(f"{notif_id}|{text}".encode()).hexdigest()[:8]
        filename     = f"LINKEDIN_{date_slug}_{text_slug}_{uniq}.md"
        filepath     = self.needs_action / filename

        received_iso = datetime.now(timezone.utc).isoformat()

        # Determine if this warrants a LinkedIn post draft
        draft_suggestion = ""
        if category == "business_opportunity":
            draft_suggestion = "- [ ] Use SKILL_LinkedIn_Draft to draft a post about this opportunity"
        elif category == "job_signal":
            draft_suggestion = "- [ ] Consider drafting a LinkedIn post showcasing relevant services"

        content = f"""\
---
type: linkedin_opportunity
linkedin_id: "{notif_id}"
category: {category}
link: "{link}"
received: "{received_iso}"
priority: {priority}
status: pending
source: linkedin
---

# LinkedIn: {category.replace('_', ' ').title()}

**Category:** {category}
**Priority:** {priority}
**Link:** {link if link else "N/A"}
**Received:** {received_iso}

---

## Notification Content

{text}

---

## Suggested Actions

- [ ] Review this LinkedIn notification
- [ ] Reply via LinkedIn (requires HITL if new contact)
{draft_suggestion}
- [ ] Log as business intelligence
- [ ] Archive if no action needed (move to Done/)

---

## Processing Notes

> _(Claude: add your analysis and action taken here before moving to Done/)_

---

*Captured by LinkedInWatcher at {received_iso}*
"""

        try:
            filepath.write_text(content, encoding="utf-8")
        except OSError as e:
            self.logger.error(f"Failed to write file {filename}: {e}")
            return None

        self.processed_ids.add(notif_id)
        self._save_state()

        self.logger.info(f"Created: {filename} | Category: {category} | Priority: {priority}")
        return filepath

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _slugify(text: str, max_len: int = 40) -> str:
        slug = re.sub(r"[^\w\s-]", "", text).strip()
        slug = re.sub(r"[\s_]+", "_", slug)
        return slug[:max_len].strip("_") or "notification"

    def shutdown(self) -> None:
        self.logger.info("LinkedInWatcher stopped.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="LinkedInWatcher — Silver AI Employee LinkedIn perception layer"
    )
    parser.add_argument("--vault", default=".", help="Path to vault root")
    parser.add_argument("--interval", type=int, default=300, help="Poll interval in seconds")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    args = parser.parse_args()

    watcher = LinkedInWatcher(
        vault_path=args.vault,
        check_interval=args.interval,
        headless=not args.no_headless,
    )
    watcher.run()
