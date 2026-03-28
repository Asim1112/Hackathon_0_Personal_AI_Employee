"""
base_watcher.py — Abstract base class for all Platinum AI Employee Watchers.

Platinum upgrade: adds `needs_action_subdir` parameter so watchers can write
to Needs_Action/email/ or Needs_Action/social/ instead of Needs_Action/ root.

All Watchers (Gmail, LinkedIn, Twitter, Facebook) inherit from BaseWatcher.
"""

import time
import logging
import signal
import sys
from pathlib import Path
from abc import ABC, abstractmethod


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Configure and return a named logger with a consistent format."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)-20s] %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(name)


class BaseWatcher(ABC):
    """
    Abstract base class for all Platinum Watcher scripts.

    Args:
        vault_path:           Root of the Obsidian/Platinum vault.
        check_interval:       Seconds between polls. Default 60.
        needs_action_subdir:  Sub-folder inside Needs_Action/ to write to.
                              "email"  → Needs_Action/email/
                              "social" → Needs_Action/social/
                              ""       → Needs_Action/  (backward compat)

    Subclasses must implement:
        check_for_updates()    → list of new raw items
        create_action_file()   → writes .md to self.needs_action
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 60,
        needs_action_subdir: str = "",
    ):
        self.vault_path     = Path(vault_path).resolve()
        self.check_interval = check_interval
        self.logger         = setup_logging(self.__class__.__name__)
        self._running       = True

        # Resolve Needs_Action path — supports subdirectory routing
        subdir = needs_action_subdir.strip("/") if needs_action_subdir else ""
        if subdir:
            self.needs_action = self.vault_path / "Needs_Action" / subdir
        else:
            self.needs_action = self.vault_path / "Needs_Action"

        self.done  = self.vault_path / "Done"
        self.inbox = self.vault_path / "Inbox"

        self._ensure_folders()
        self._register_signals()

    # ------------------------------------------------------------------
    # Folder bootstrap
    # ------------------------------------------------------------------

    def _ensure_folders(self) -> None:
        """Create required vault folders if they don't exist yet."""
        for folder in (self.needs_action, self.done):
            folder.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Graceful shutdown
    # ------------------------------------------------------------------

    def _register_signals(self) -> None:
        """Catch SIGINT/SIGTERM so the loop exits cleanly.
        Silently skips when called from a daemon thread (orchestrator handles this)."""
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                signal.signal(sig, self._handle_signal)
        except ValueError:
            self.logger.debug(
                "Signal registration skipped — not in main thread "
                "(orchestrator handles shutdown)"
            )

    def _handle_signal(self, signum, frame) -> None:
        self.logger.info(f"Received signal {signum} — shutting down gracefully.")
        self._running = False

    def shutdown(self) -> None:
        """Override in subclass to release resources on exit."""
        pass

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def check_for_updates(self) -> list:
        """Poll the source and return a list of new raw items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Convert one raw item into a .md file inside self.needs_action."""
        pass

    # ------------------------------------------------------------------
    # Main run loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Blocking poll → process → sleep loop with full error recovery."""
        self.logger.info(
            f"Starting {self.__class__.__name__} "
            f"| vault={self.vault_path} "
            f"| needs_action={self.needs_action} "
            f"| interval={self.check_interval}s"
        )

        while self._running:
            try:
                items = self.check_for_updates()
                if items:
                    self.logger.info(f"Found {len(items)} new item(s) to process.")
                for item in items:
                    if not self._running:
                        break
                    try:
                        path = self.create_action_file(item)
                        if path:
                            self.logger.info(f"Action file created: {path.name}")
                    except Exception as item_err:
                        self.logger.error(f"Failed to process item: {item_err}", exc_info=True)
            except Exception as poll_err:
                self.logger.error(f"Poll error: {poll_err}", exc_info=True)

            if self._running:
                self.logger.debug(f"Sleeping {self.check_interval}s until next poll…")
                time.sleep(self.check_interval)

        self.shutdown()
        self.logger.info(f"{self.__class__.__name__} stopped.")
