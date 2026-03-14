"""
whatsapp_watcher.py — WhatsApp Watcher for the Silver-tier AI Employee.

Polls WhatsApp Web for unread messages containing business-relevant keywords.
Extends BaseWatcher from base_watcher.py (Bronze/Silver pattern).

Uses Playwright's launch_persistent_context so the WhatsApp Web session
(QR scan auth) survives across process restarts — scan once, runs forever.

Architecture:
    Playwright → WhatsApp Web → Needs_Action/ → Claude (Reasoning) → Done/

Keyword filter (configurable):
    ['urgent', 'asap', 'invoice', 'payment', 'help']
    — Only messages containing at least one keyword create an action file.
    — All others are silently skipped (logged at DEBUG).

Deduplication:
    A SHA-256 hash of (sender + preview_text) is persisted to
    .whatsapp_watcher_state.json. The same message preview is never written
    twice, even across restarts.

Priority mapping:
    urgent / asap / deadline / overdue / legal → urgent
    invoice / payment / contract / proposal    → high
    help / question / follow-up               → medium
    (keyword match but no above trigger)       → medium

HITL: WhatsApp sends (replies) are NEVER made by this watcher.
    Drafts are written to Needs_Action/ for Claude to process.
    Silver tier: new contacts and messages with financial content
    are escalated to Pending_Approval/ by SKILL_Gmail_Triage.

Usage:
    # First run — show browser window so you can scan the QR code
    python whatsapp_watcher.py --no-headless

    # Subsequent runs — fully headless (session restored from disk)
    python whatsapp_watcher.py

    # Custom vault path and poll interval
    python whatsapp_watcher.py --vault /path/to/silver --interval 60

Setup:
    1. uv sync  (playwright already in pyproject.toml)
    2. uv run playwright install chromium  (one-time browser download)
    3. python whatsapp_watcher.py --no-headless
       → Browser opens WhatsApp Web → scan QR with your phone
       → Session saved to whatsapp_session/ folder
    4. Close (Ctrl-C) and re-run headless:
       python whatsapp_watcher.py

Dependencies (pyproject.toml):
    playwright>=1.49.0
    python-dotenv>=1.0.0

Notes:
    - WhatsApp Web reads message PREVIEWS from the chat list — it does NOT
      click into chats, so messages remain "unread" on your phone.
    - Playwright persistent context stores cookies/localStorage to disk,
      keeping WhatsApp logged in between runs.
    - WhatsApp may occasionally show a "Use Here" popup if another device
      connects — the watcher handles this automatically.
    - WhatsApp ToS: use this for personal business automation only.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

try:
    from playwright.sync_api import (
        BrowserContext,
        Page,
        sync_playwright,
        TimeoutError as PWTimeoutError,
    )
except ImportError:
    print(
        "ERROR: playwright not installed.\n"
        "Run: uv sync && uv run playwright install chromium",
        file=sys.stderr,
    )
    sys.exit(1)

from base_watcher import BaseWatcher


# ---------------------------------------------------------------------------
# Keyword configuration
# ---------------------------------------------------------------------------

#: Messages are only captured if they contain at least one of these words.
FILTER_KEYWORDS: list[str] = ["urgent", "asap", "invoice", "payment", "help"]

#: Priority tiers — first match wins (most urgent first).
PRIORITY_TIERS: list[tuple[str, list[str]]] = [
    ("urgent", ["urgent", "asap", "immediately", "critical", "deadline",
                "overdue", "legal", "lawsuit", "final notice", "action required"]),
    ("high",   ["invoice", "payment", "contract", "proposal", "refund",
                "chargeback", "dispute", "overdue"]),
    ("medium", ["help", "question", "query", "follow up", "follow-up",
                "checking in", "update"]),
]

# ---------------------------------------------------------------------------
# WhatsApp Web selectors
#
# WhatsApp updates its DOM frequently. We use ordered fallback lists so the
# watcher keeps working even when specific data-testid attributes disappear.
# If all selectors in a list fail, the watcher warns and skips the poll.
# ---------------------------------------------------------------------------

# Chat list sidebar — try each in order until one is visible
CHAT_LIST_SELECTORS: list[str] = [
    "#pane-side",                           # Stable left-sidebar ID (most reliable)
    '[aria-label="Chat list"]',             # Aria label on the list container
    '[data-testid="chat-list"]',            # Old data-testid (may be gone)
    'div[tabindex="-1"] > div > div',       # Generic structural fallback
]

# Individual chat rows inside the sidebar
CHAT_ROW_SELECTORS: list[str] = [
    '[data-testid="cell-frame-container"]',
    "div#pane-side > div > div > div",      # Structural fallback
]

# Sender name inside a chat row
CHAT_TITLE_SELECTORS: list[str] = [
    '[data-testid="cell-frame-title"]',
    "span[title]",                          # WhatsApp renders names in span[title]
    "span[dir='auto']",
]

# Last message preview inside a chat row
LAST_MSG_SELECTORS: list[str] = [
    '[data-testid="last-msg-text"]',
    "span[class*='_11JPr']",               # Internal class (changes with deploys)
    "div[role='gridcell'] span",
]

# Unread count badge inside a chat row
UNREAD_BADGE_SELECTORS: list[str] = [
    '[data-testid="icon-unread-count"]',
    'span[aria-label*="unread"]',
    "span[data-icon='unread-count']",
    "div[aria-label*='unread']",
]

# Dismiss "Use Here" popup (WhatsApp opened on another device)
SEL_USE_HERE_BTN = 'div[role="button"]:has-text("Use Here")'

# QR code canvas shown on first launch / session expiry
SEL_QR_CODE = (
    'canvas[aria-label="Scan this QR code to link a device"], '
    '[data-testid="qrcode"]'
)

WHATSAPP_WEB_URL     = "https://web.whatsapp.com"
CHAT_LIST_TIMEOUT_MS = 90_000   # 90 s — allow ample time for post-QR-scan load
POLL_TIMEOUT_MS      = 10_000   # 10 s — page is already open, should be fast


# ---------------------------------------------------------------------------
# WhatsAppWatcher
# ---------------------------------------------------------------------------

class WhatsAppWatcher(BaseWatcher):
    """
    Polls WhatsApp Web for unread messages whose previews contain any of
    FILTER_KEYWORDS, and writes structured .md files to Needs_Action/.

    Inherits the run() loop, signal handling, and folder bootstrapping from
    BaseWatcher. Overrides check_for_updates() and create_action_file().

    The Playwright browser is opened once and kept alive across all polls,
    avoiding the overhead of a fresh launch on every check_interval.

    Args:
        vault_path:     Root directory of the Silver vault.
        session_path:   Directory where Playwright stores browser session data
                        (cookies, localStorage). Created automatically.
                        Default: <vault_path>/whatsapp_session
        check_interval: Seconds between WhatsApp polls. Default 30.
        headless:       Run Chromium without a visible window. Set False for
                        first run to scan the QR code. Default True.
        keywords:       Keyword filter list. Default FILTER_KEYWORDS.
    """

    def __init__(
        self,
        vault_path: str = ".",
        session_path: Optional[str] = None,
        check_interval: int = 30,
        headless: bool = True,
        keywords: Optional[list[str]] = None,
    ) -> None:
        super().__init__(vault_path, check_interval)

        self.session_path: Path = (
            Path(session_path)
            if session_path
            else self.vault_path / "whatsapp_session"
        )
        self.headless = headless
        self.keywords = [kw.lower() for kw in (keywords or FILTER_KEYWORDS)]

        # Deduplication: persist hashes of processed message previews
        self.state_path: Path = self.vault_path / ".whatsapp_watcher_state.json"
        self.processed_hashes: set[str] = self._load_state()

        # Playwright objects — initialised lazily in _ensure_browser()
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        # Caches whichever CHAT_LIST_SELECTORS entry worked last, so we try
        # it first on the next poll (avoids cycling through all fallbacks).
        self._active_chat_list_sel: Optional[str] = None

        self.logger.info(
            f"WhatsAppWatcher ready | "
            f"session={self.session_path} | "
            f"headless={self.headless} | "
            f"keywords={self.keywords}"
        )

    # ------------------------------------------------------------------
    # State persistence (deduplication)
    # ------------------------------------------------------------------

    def _load_state(self) -> set[str]:
        """Load previously seen message hashes from disk."""
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                hashes = set(data.get("processed_hashes", []))
                self.logger.info(
                    f"Loaded {len(hashes)} processed message hash(es) from state"
                )
                return hashes
            except (json.JSONDecodeError, KeyError) as exc:
                self.logger.warning(f"Could not read state file ({exc}) — starting fresh")
        return set()

    def _save_state(self) -> None:
        """Persist processed hashes to disk."""
        self.state_path.write_text(
            json.dumps(
                {"processed_hashes": sorted(self.processed_hashes)},
                indent=2,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _make_hash(sender: str, preview: str) -> str:
        """
        Produce a stable, short deduplication key from sender + preview text.
        SHA-256 first 16 hex chars is collision-resistant enough for this use.
        """
        raw = f"{sender.strip().lower()}|{preview.strip().lower()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    # ------------------------------------------------------------------
    # Browser lifecycle (keep-alive across polls)
    # ------------------------------------------------------------------

    def _ensure_browser(self) -> Page:
        """
        Start Playwright + persistent context if not already running.
        Returns a ready Page pointing at WhatsApp Web.
        """
        if self._page and not self._page.is_closed():
            return self._page

        self.logger.info("Launching Playwright Chromium (persistent context)...")

        self.session_path.mkdir(parents=True, exist_ok=True)

        self._playwright = sync_playwright().start()

        self._context = self._playwright.chromium.launch_persistent_context(
            str(self.session_path),
            headless=self.headless,
            # Mimic a realistic desktop browser to avoid bot detection
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-GB",
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )

        # Reuse an existing page or open a new one
        self._page = (
            self._context.pages[0]
            if self._context.pages
            else self._context.new_page()
        )

        self._navigate_to_whatsapp()
        return self._page

    def _first_matching_selector(self, page: "Page", selectors: list[str], timeout_ms: int) -> Optional[str]:
        """
        Try each selector in order with a short per-selector timeout.
        Returns the first selector that finds a visible element, or None.
        The total wall-clock time is at most timeout_ms.
        """
        import time
        per_sel_ms  = max(1_000, timeout_ms // max(len(selectors), 1))
        deadline    = time.monotonic() + timeout_ms / 1000.0

        for sel in selectors:
            remaining_ms = int((deadline - time.monotonic()) * 1000)
            if remaining_ms <= 0:
                break
            try:
                page.wait_for_selector(sel, timeout=min(per_sel_ms, remaining_ms))
                self.logger.debug(f"Selector matched: {sel!r}")
                return sel
            except PWTimeoutError:
                self.logger.debug(f"Selector not found: {sel!r}")
                continue
            except Exception as exc:
                self.logger.debug(f"Selector error ({sel!r}): {exc}")
                continue
        return None

    def _navigate_to_whatsapp(self) -> None:
        """
        Navigate to WhatsApp Web and wait for the chat list using fallback
        selectors. Handles:
          - QR code screen (headless=False first-run, session expired)
          - "Use Here" multi-device popup
          - Normal already-logged-in load
          - WhatsApp DOM changes (selector list in CHAT_LIST_SELECTORS)
        """
        page = self._page
        self.logger.info(f"Navigating to {WHATSAPP_WEB_URL}")
        page.goto(WHATSAPP_WEB_URL, wait_until="domcontentloaded")

        # Dismiss "Use Here" popup (WhatsApp opened on another browser/device)
        try:
            use_here = page.wait_for_selector(SEL_USE_HERE_BTN, timeout=3_000)
            if use_here:
                self.logger.info('Dismissing "Use Here" popup')
                use_here.click()
        except PWTimeoutError:
            pass  # No popup — normal

        # Detect QR code screen (first run or session expired)
        try:
            qr = page.wait_for_selector(SEL_QR_CODE, timeout=4_000)
            if qr:
                if self.headless:
                    self.logger.error(
                        "WhatsApp QR code detected in headless mode.\n"
                        "  Fix: run once with --no-headless to scan the QR code,\n"
                        "  then restart normally. Session will be saved automatically."
                    )
                    self._teardown()
                    sys.exit(1)
                else:
                    self.logger.info(
                        "QR code displayed — scan it with your phone now.\n"
                        "Waiting up to 90 seconds for you to scan..."
                    )
        except PWTimeoutError:
            pass  # Already logged in — no QR shown

        # Wait for the chat list using multiple fallback selectors
        matched = self._first_matching_selector(
            page, CHAT_LIST_SELECTORS, timeout_ms=CHAT_LIST_TIMEOUT_MS
        )
        if matched:
            self.logger.info(f"WhatsApp Web loaded — session active (matched: {matched!r})")
            self._active_chat_list_sel = matched  # remember which one worked
        else:
            # Non-fatal: log and let the poll skip rather than crashing the loop
            self.logger.warning(
                "Chat list did not appear within timeout. "
                "WhatsApp may still be loading — will retry on next poll interval.\n"
                "If this persists: run with --no-headless to inspect the browser state."
            )
            # Mark page as unusable so _ensure_browser() relaunches next time
            self._page = None

    # ------------------------------------------------------------------
    # BaseWatcher interface — check_for_updates
    # ------------------------------------------------------------------

    def _query_any(self, element, selectors: list[str]) -> Optional[object]:
        """Try each selector against an element, return the first match or None."""
        for sel in selectors:
            try:
                el = element.query_selector(sel)
                if el:
                    return el
            except Exception:
                continue
        return None

    def check_for_updates(self) -> list[dict]:
        """
        Scan the WhatsApp Web chat list for unread chats whose preview
        text contains at least one keyword in self.keywords.

        Returns a list of message dicts (new/unseen only).
        Does NOT click into any chat — reads the sidebar preview only,
        so messages stay "unread" on the phone.

        Key behaviour:
          - NO page.reload() on every poll — the page stays loaded between
            intervals. Reloading re-triggers the login flow and is the root
            cause of the previous timeout errors.
          - If the page has somehow navigated away from WhatsApp Web, we
            navigate back (without a full browser restart).
          - Uses fallback selector lists for chat rows, titles, previews and
            unread badges so the watcher survives WhatsApp DOM updates.
        """
        page = self._ensure_browser()
        if page is None:
            # _navigate_to_whatsapp failed — will retry on next interval
            return []

        # Verify we're still on WhatsApp Web (guards against unexpected navigation)
        if "web.whatsapp.com" not in page.url:
            self.logger.info("Page left WhatsApp Web — navigating back...")
            self._navigate_to_whatsapp()
            if self._page is None:
                return []
            page = self._page

        # Confirm the chat list is still rendered (no full reload needed)
        active_sel = getattr(self, "_active_chat_list_sel", None)
        candidates = ([active_sel] + CHAT_LIST_SELECTORS) if active_sel else CHAT_LIST_SELECTORS
        matched = self._first_matching_selector(page, candidates, timeout_ms=POLL_TIMEOUT_MS)
        if not matched:
            self.logger.warning("Chat list not visible — skipping this poll")
            return []

        # Dismiss any "Use Here" popup that appeared since last poll
        try:
            btn = page.wait_for_selector(SEL_USE_HERE_BTN, timeout=1_500)
            if btn:
                self.logger.info('Dismissing "Use Here" popup mid-poll')
                btn.click()
        except PWTimeoutError:
            pass

        # ── Collect chat rows ────────────────────────────────────────────────
        chat_rows = []
        for row_sel in CHAT_ROW_SELECTORS:
            try:
                rows = page.query_selector_all(row_sel)
                if rows:
                    chat_rows = rows
                    self.logger.debug(f"Chat rows ({len(rows)}) via {row_sel!r}")
                    break
            except Exception:
                continue

        if not chat_rows:
            self.logger.warning("No chat rows found — WhatsApp DOM may have changed")
            return []

        # ── Scan rows for unread + keyword matches ───────────────────────────
        messages:    list[dict] = []
        total_unread = 0

        for row in chat_rows:
            try:
                # Unread badge — try each selector
                badge = self._query_any(row, UNREAD_BADGE_SELECTORS)
                if not badge:
                    continue
                total_unread += 1

                unread_count_text = badge.inner_text().strip() or "?"

                # Sender name — try each selector, also check span[title] attribute
                title_el = self._query_any(row, CHAT_TITLE_SELECTORS)
                if title_el:
                    # prefer the title attribute (renders the full name without ellipsis)
                    sender = title_el.get_attribute("title") or title_el.inner_text().strip()
                else:
                    sender = "Unknown"

                # Message preview — try each selector
                preview_el = self._query_any(row, LAST_MSG_SELECTORS)
                preview    = preview_el.inner_text().strip() if preview_el else ""

                # If we got nothing useful, fall back to the whole row text
                if not sender and not preview:
                    row_text = row.inner_text().strip()
                    lines    = [l.strip() for l in row_text.splitlines() if l.strip()]
                    sender   = lines[0] if lines else "Unknown"
                    preview  = " ".join(lines[1:]) if len(lines) > 1 else ""

                # Keyword filter
                combined = f"{sender} {preview}".lower()
                if not any(kw in combined for kw in self.keywords):
                    self.logger.debug(f"Skipping unread from '{sender}' — no keyword match")
                    continue

                # Deduplication
                msg_hash = self._make_hash(sender, preview)
                if msg_hash in self.processed_hashes:
                    self.logger.debug(f"Skipping already-seen message from '{sender}'")
                    continue

                messages.append({
                    "hash":             msg_hash,
                    "sender":           sender,
                    "preview":          preview,
                    "unread_count":     unread_count_text,
                    "matched_keywords": [kw for kw in self.keywords if kw in combined],
                })

            except Exception as exc:
                self.logger.warning(f"Error reading chat row: {exc}")
                continue

        self.logger.info(
            f"WhatsApp poll: {total_unread} unread chats scanned, "
            f"{len(messages)} new keyword-matching message(s)"
        )
        return messages

    # ------------------------------------------------------------------
    # BaseWatcher interface — create_action_file
    # ------------------------------------------------------------------

    def create_action_file(self, message: dict) -> Optional[Path]:
        """
        Write a structured .md file to Needs_Action/ for one WhatsApp message.

        YAML frontmatter fields:
            type, from, text, received, priority, status, source,
            unread_count, matched_keywords, whatsapp_hash
        """
        sender        = message["sender"]
        preview       = message["preview"]
        msg_hash      = message["hash"]
        unread_count  = message.get("unread_count", "?")
        matched_kws   = message.get("matched_keywords", [])

        priority     = self._detect_priority(preview, sender)
        received_iso = datetime.now(timezone.utc).isoformat()
        date_slug    = datetime.now().strftime("%Y-%m-%d")
        sender_slug  = self._slugify(sender, max_len=30)
        filename     = f"WHATSAPP_{date_slug}_{sender_slug}_{msg_hash}.md"
        filepath     = self.needs_action / filename

        # Escape YAML special characters in string fields
        def _esc(s: str) -> str:
            return s.replace('"', '\\"').replace("\n", " ")

        content = f"""\
---
type: whatsapp
whatsapp_hash: "{msg_hash}"
from: "{_esc(sender)}"
text: "{_esc(preview)}"
received: "{received_iso}"
priority: {priority}
status: pending
source: whatsapp
unread_count: "{unread_count}"
matched_keywords: [{", ".join(matched_kws)}]
---

# WhatsApp: {sender}

**From:** {sender}
**Received:** {received_iso}
**Unread messages:** {unread_count}
**Priority:** {priority}
**Matched keywords:** {", ".join(matched_kws) or "—"}

---

## Message Preview

> {preview}

> ⚠️ This is the chat list preview only. Open WhatsApp to read the full message.
> The watcher does NOT click into chats — messages remain unread on your phone.

---

## Suggested Actions

- [ ] Open WhatsApp and read the full message thread
- [ ] Draft a reply (use SKILL_Gmail_Triage rules for tone and HITL rules)
- [ ] If new contact → move to Pending_Approval/ before replying
- [ ] If financial content (invoice/payment) → move to Pending_Approval/ (£50 rule)
- [ ] If complaint/legal keyword → HUMAN_REVIEW immediately
- [ ] Log if no action required, then move to Done/

---

## Processing Notes

> _(Claude: add your analysis and action taken here before moving to Done/)_

---

*Captured by WhatsAppWatcher at {received_iso}*
"""

        try:
            filepath.write_text(content, encoding="utf-8")
        except OSError as exc:
            self.logger.error(f"Failed to write {filename}: {exc}")
            return None

        # Mark as seen and persist
        self.processed_hashes.add(msg_hash)
        self._save_state()

        self.logger.info(
            f"Created: {filename} | From: {sender} | "
            f"Priority: {priority} | Keywords: {matched_kws}"
        )
        return filepath

    # ------------------------------------------------------------------
    # Priority detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_priority(text: str, sender: str = "") -> str:
        """
        Scan message text (and optionally sender name) against priority tiers.
        Returns the tier label of the first match, or 'medium' if nothing matches.
        """
        combined = f"{text} {sender}".lower()
        for priority_label, keywords in PRIORITY_TIERS:
            if any(kw in combined for kw in keywords):
                return priority_label
        return "medium"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _slugify(text: str, max_len: int = 40) -> str:
        """Convert text to a safe, readable filename segment."""
        slug = re.sub(r"[^\w\s-]", "", text).strip()
        slug = re.sub(r"[\s_]+", "_", slug)
        return slug[:max_len].strip("_") or "chat"

    # ------------------------------------------------------------------
    # Graceful shutdown
    # ------------------------------------------------------------------

    def _teardown(self) -> None:
        """Close Playwright resources cleanly."""
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._context   = None
        self._page      = None
        self._playwright = None

    def shutdown(self) -> None:
        """Called by BaseWatcher.run() on graceful exit."""
        self.logger.info("Closing Playwright browser...")
        self._teardown()
        self.logger.info("WhatsAppWatcher stopped.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "WhatsAppWatcher — Silver AI Employee WhatsApp perception layer.\n\n"
            "FIRST RUN:  python whatsapp_watcher.py --no-headless\n"
            "            (scan QR code when browser opens, then Ctrl-C)\n\n"
            "SUBSEQUENT: python whatsapp_watcher.py\n"
            "            (session restored automatically, runs headless)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--vault",
        default=".",
        help="Path to Silver vault root (default: current directory)",
    )
    parser.add_argument(
        "--session",
        default=None,
        help=(
            "Path to Playwright session directory "
            "(default: <vault>/whatsapp_session)"
        ),
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds between WhatsApp polls (default: 30)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        dest="no_headless",
        help="Show browser window — required for first-run QR scan",
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=None,
        metavar="WORD",
        help=(
            "Override keyword filter (default: urgent asap invoice payment help). "
            "Example: --keywords urgent invoice contract"
        ),
    )
    args = parser.parse_args()

    watcher = WhatsAppWatcher(
        vault_path=args.vault,
        session_path=args.session,
        check_interval=args.interval,
        headless=not args.no_headless,
        keywords=args.keywords,
    )
    watcher.run()
