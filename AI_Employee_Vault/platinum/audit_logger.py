"""
audit_logger.py — Platinum Tier Shared Audit Logging Utility

Writes structured JSON log entries to Logs/YYYY-MM-DD.json.
Used by all Python watchers and orchestrators in platinum/.

Log format:
{
    "timestamp": "2026-03-28T14:32:00.000Z",
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

# Vault root is always the directory containing this file (platinum/)
VAULT_ROOT = Path(__file__).parent
LOGS_DIR   = VAULT_ROOT / "Logs"


def _today_log_path() -> Path:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return LOGS_DIR / f"{date_str}.json"


def _read_log(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    try:
        text = log_path.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else []
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read log file %s: %s", log_path, exc)
        return []


def _write_log(log_path: Path, entries: list[dict]) -> None:
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
    """Append a single audit log entry to today's log file."""
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
    entries  = _read_log(log_path)
    entries.append(entry)
    _write_log(log_path, entries)
    logger.debug("Audit log: %s → %s [%s]", action_type, target, result)
    return entry


def log_watcher_start(watcher_name: str) -> dict:
    return log_action("watcher_started", watcher_name, watcher_name,
                      notes=f"{watcher_name} started")


def log_watcher_stop(watcher_name: str, reason: str = "shutdown") -> dict:
    return log_action("watcher_stopped", watcher_name, watcher_name,
                      notes=f"{watcher_name} stopped — {reason}")


def log_error(source: str, target: str | None, error: str) -> dict:
    return log_action("error", source, target, result="failure", notes=error)


def get_todays_entries() -> list[dict]:
    return _read_log(_today_log_path())
