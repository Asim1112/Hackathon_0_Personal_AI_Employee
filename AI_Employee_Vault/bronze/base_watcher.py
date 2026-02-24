"""
base_watcher.py — Abstract base class for all AI Employee Watchers.

All Watchers (Gmail, WhatsApp, FileSystem, etc.) inherit from BaseWatcher.
Pattern from: F:\\Watcher\\watcher.md
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
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(name)


class BaseWatcher(ABC):
    """
    Abstract base class for all Watcher scripts.

    Subclasses must implement:
        - check_for_updates() -> list   : poll source, return new raw items
        - create_action_file(item) -> Path : write a .md file to Needs_Action/

    The run() loop handles timing, error recovery, and graceful shutdown.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path    = Path(vault_path).resolve()
        self.needs_action  = self.vault_path / "Needs_Action"
        self.done          = self.vault_path / "Done"
        self.inbox         = self.vault_path / "Inbox"
        self.check_interval = check_interval
        self.logger        = setup_logging(self.__class__.__name__)
        self._running      = True

        self._ensure_folders()
        self._register_signals()

    # ------------------------------------------------------------------
    # Folder bootstrap
    # ------------------------------------------------------------------

    def _ensure_folders(self) -> None:
        """Create vault folders if they don't exist yet."""
        for folder in (self.needs_action, self.done, self.inbox):
            folder.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Graceful shutdown
    # ------------------------------------------------------------------

    def _register_signals(self) -> None:
        """Catch SIGINT / SIGTERM so the loop exits cleanly."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_signal)

    def _handle_signal(self, signum, frame) -> None:
        self.logger.info(f"Received signal {signum} — shutting down gracefully.")
        self._running = False

    def shutdown(self) -> None:
        """Override in subclass to release resources on exit."""
        pass

    # ------------------------------------------------------------------
    # Abstract interface — must implement in subclass
    # ------------------------------------------------------------------

    @abstractmethod
    def check_for_updates(self) -> list:
        """Poll the source and return a list of new raw items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """
        Convert one raw item into a .md file inside Needs_Action/.
        Returns the Path of the file created (or None on failure).
        """
        pass

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Blocking loop: poll → process → sleep → repeat.
        Catches all exceptions so a single bad item cannot kill the watcher.
        """
        self.logger.info(
            f"Starting {self.__class__.__name__} "
            f"| vault={self.vault_path} "
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
                        self.logger.error(
                            f"Failed to process item: {item_err}", exc_info=True
                        )

            except Exception as poll_err:
                self.logger.error(f"Poll error: {poll_err}", exc_info=True)

            if self._running:
                self.logger.debug(f"Sleeping {self.check_interval}s until next poll…")
                time.sleep(self.check_interval)

        self.shutdown()
        self.logger.info(f"{self.__class__.__name__} stopped.")
