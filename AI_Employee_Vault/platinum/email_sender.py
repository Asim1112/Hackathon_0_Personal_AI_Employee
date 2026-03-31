"""
email_sender.py — Platinum Local Agent Acknowledgment Processor

Watches platinum/Approved/ for .md files and processes NON-EMAIL types:
  type: draft_reply       → SKIP — email-mcp (Node.js) is the sole email sender
  type: approval_request  → acknowledge + archive to Done/
  other                   → archive with note to Done/

email-mcp (Node.js, mcp_servers/email-mcp/) owns ALL email sending via SMTP.
This script handles ONLY acknowledgment and archiving of non-email approved items.

Usage:
  uv run python email_sender.py           # daemon (polls every 10s)
  uv run python email_sender.py --once    # process current files then exit
"""

import argparse
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────

VAULT = Path(__file__).parent.resolve()
load_dotenv(VAULT / ".env")

POLL_INTERVAL = 10  # seconds

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [email-sender] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("email_sender")

# ── Frontmatter parser ────────────────────────────────────────────────────────

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML-style frontmatter. Returns (meta_dict, body_text)."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)", content, re.DOTALL)
    if not m:
        return {}, content
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([\w_-]+):\s*(.+?)\s*$", line)
        if kv:
            meta[kv.group(1)] = kv.group(2).strip('"').strip("'")
    return meta, m.group(2).strip()

# ── Audit log (hackathon-compliant schema) ────────────────────────────────────

def log_action(action_type: str, target: str, parameters: dict, result: str) -> None:
    """Append a compliant entry to today's Logs/YYYY-MM-DD.json.

    Schema matches hackathon requirement exactly:
      timestamp, action_type, actor, target, parameters,
      approval_status, approved_by, result
    """
    log_dir = VAULT / "Logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "action_type":     action_type,
        "actor":           "local_agent",
        "target":          target,
        "parameters":      parameters,
        "approval_status": "approved",
        "approved_by":     "human",
        "result":          result,
    }

    entries: list = []
    if log_file.exists():
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
            if not isinstance(entries, list):
                entries = []
        except Exception:
            entries = []

    entries.append(entry)
    log_file.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")

# ── File move helper ──────────────────────────────────────────────────────────

def move_to_done(src: Path, original_content: str, note: str) -> None:
    """Update status field and move src → Done/ with appended note."""
    done_dir = VAULT / "Done"
    done_dir.mkdir(exist_ok=True)

    updated = re.sub(
        r"^(status:\s*)pending\s*$", r"\1done",
        original_content, flags=re.MULTILINE
    )
    updated += f"\n\n---\n\n**{note}**\n"

    dest = done_dir / src.name
    dest.write_text(updated, encoding="utf-8")
    src.unlink()
    log.info("Archived → Done/%s", src.name)

# ── Core processor ────────────────────────────────────────────────────────────

def process_file(f: Path) -> None:
    """Process one .md file from Approved/ based on its type field."""
    log.info("─── Processing: %s", f.name)

    try:
        content = f.read_text(encoding="utf-8")
    except Exception as e:
        log.error("Could not read %s: %s", f.name, e)
        return

    meta, body  = parse_frontmatter(content)
    file_type   = meta.get("type", "unknown")
    now_iso     = datetime.now(timezone.utc).isoformat()

    # ── draft_reply: owned by email-mcp — do not touch ───────────────────────
    if file_type == "draft_reply":
        log.info(
            "Skipping %s — type: draft_reply is delegated to email-mcp (Node.js)",
            f.name,
        )
        # Do NOT move or modify — email-mcp will process and move to Done/
        return

    # ── approval_request: acknowledge + archive ───────────────────────────────
    elif file_type == "approval_request":
        from_   = meta.get("from", "unknown sender")
        subject = meta.get("subject", "(no subject)")
        note    = f"Acknowledged by Local Agent {now_iso} — informational, no reply required"
        move_to_done(f, content, note)
        log_action(
            action_type="email_acknowledged",
            target=from_,
            parameters={"subject": subject, "file": f.name},
            result="success",
        )
        log.info("✓ Acknowledged: [%s] from %s", subject, from_)

    # ── all other types: archive with note ────────────────────────────────────
    else:
        note = f"Processed by Local Agent {now_iso} (type: {file_type})"
        move_to_done(f, content, note)
        log_action(
            action_type="file_processed",
            target=f.name,
            parameters={"type": file_type, "file": f.name},
            result="success",
        )
        log.info("✓ Archived (type=%s): %s", file_type, f.name)

# ── Watcher loop ──────────────────────────────────────────────────────────────

def watch_approved(once: bool = False) -> None:
    """
    Poll Approved/ every POLL_INTERVAL seconds.
    Skips draft_reply files — those are handled by email-mcp.
    Called directly or imported by local_orchestrator as a daemon thread.
    """
    approved = VAULT / "Approved"
    approved.mkdir(exist_ok=True)
    seen: set[str] = set()

    log.info(
        "Watching %s (every %ds) | draft_reply → email-mcp | approval_request → Done/",
        approved, POLL_INTERVAL,
    )

    while True:
        try:
            for f in sorted(approved.glob("*.md")):
                if f.name not in seen:
                    seen.add(f.name)
                    process_file(f)
        except Exception as e:
            log.error("Watcher error: %s", e)

        if once:
            break
        time.sleep(POLL_INTERVAL)

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Platinum Local Agent Acknowledgment Processor"
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Process all files currently in Approved/ then exit"
    )
    args = parser.parse_args()

    log.info("Platinum Email Sender | Vault: %s | Agent: local_agent", VAULT)
    watch_approved(once=args.once)


if __name__ == "__main__":
    main()
