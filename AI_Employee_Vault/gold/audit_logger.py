"""
audit_logger.py — Gold Tier Shared Audit Logging Utility

Writes structured JSON log entries to Logs/YYYY-MM-DD.json.
Used by all Python watchers and can be imported anywhere in the gold tier.

Log format:
{
    "timestamp": "2026-03-11T14:32:00.000Z",
    "action_type": "<string>",
    "source": "<string>",
    "target": "<string or null>",
    "skill_used": "<string or null>",
    "approval_status": "not_required | pending | approved | rejected",
    "result": "success | failure | partial",
    "notes": "<string or null>"
}
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Vault root is always the directory containing this file
VAULT_ROOT = Path(__file__).parent
LOGS_DIR = VAULT_ROOT / "Logs"


def _today_log_path() -> Path:
    """Return the path to today's log file (UTC date)."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return LOGS_DIR / f"{date_str}.json"


def _read_log(log_path: Path) -> list[dict]:
    """Read existing log file, returning empty list if missing or invalid."""
    if not log_path.exists():
        return []
    try:
        text = log_path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        return json.loads(text)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read log file %s: %s", log_path, exc)
        return []


def _write_log(log_path: Path, entries: list[dict]) -> None:
    """Write log entries to file, creating Logs/ directory if needed."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def log_action(
    action_type: str,
    source: str,
    target: str | None = None,
    skill_used: str | None = None,
    approval_status: str = "not_required",
    result: str = "success",
    notes: str | None = None,
) -> dict:
    """
    Append a single audit log entry to today's log file.

    Args:
        action_type:     Event type string (e.g. "email_sent", "odoo_draft_created")
        source:          What wrote this entry (e.g. "gmail_watcher", "claude_code")
        target:          What was acted on (file path, email address, etc.)
        skill_used:      Skill name if triggered via a SKILL_*.md (or None)
        approval_status: One of "not_required", "pending", "approved", "rejected"
        result:          One of "success", "failure", "partial"
        notes:           Optional free-text detail

    Returns:
        The entry dict that was written.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "action_type": action_type,
        "source": source,
        "target": target,
        "skill_used": skill_used,
        "approval_status": approval_status,
        "result": result,
        "notes": notes,
    }

    log_path = _today_log_path()
    entries = _read_log(log_path)
    entries.append(entry)
    _write_log(log_path, entries)

    logger.debug("Audit log: %s → %s [%s]", action_type, target, result)
    return entry


def log_watcher_start(watcher_name: str) -> dict:
    """Convenience: log that a watcher process has started."""
    return log_action(
        action_type="watcher_started",
        source=watcher_name,
        target=watcher_name,
        notes=f"{watcher_name} started",
    )


def log_watcher_stop(watcher_name: str, reason: str = "shutdown") -> dict:
    """Convenience: log that a watcher process has stopped."""
    return log_action(
        action_type="watcher_stopped",
        source=watcher_name,
        target=watcher_name,
        notes=f"{watcher_name} stopped — {reason}",
    )


def log_error(source: str, target: str | None, error: str) -> dict:
    """Convenience: log an exception or failure."""
    return log_action(
        action_type="error",
        source=source,
        target=target,
        result="failure",
        notes=error,
    )


def get_todays_entries() -> list[dict]:
    """Return all log entries for today (for use in briefings/dashboards)."""
    return _read_log(_today_log_path())


def get_entries_for_date(date_str: str) -> list[dict]:
    """Return log entries for a specific date (YYYY-MM-DD)."""
    log_path = LOGS_DIR / f"{date_str}.json"
    return _read_log(log_path)


def get_entries_last_n_days(n: int = 7) -> list[dict]:
    """Return all log entries from the last N days, newest first."""
    all_entries: list[dict] = []
    now = datetime.now(timezone.utc)
    for i in range(n):
        from datetime import timedelta
        day = now - timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        all_entries.extend(get_entries_for_date(date_str))
    # Sort newest first
    all_entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return all_entries
