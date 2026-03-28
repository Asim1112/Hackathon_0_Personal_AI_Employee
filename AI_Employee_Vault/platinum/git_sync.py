"""
git_sync.py — Safe Git sync utility for Platinum agents.

Used by both cloud_orchestrator.py and local_orchestrator.py.
Always pull before reading vault, always push after writing.

Usage:
    from git_sync import sync_pull, sync_push

    sync_pull()
    # ... do work ...
    sync_push("cloud: drafted reply for email from John Smith")
"""

import logging
import os
import subprocess
from pathlib import Path

log      = logging.getLogger("git_sync")
# platinum/ is one level below the vault root (AI_Employee_Vault/)
PLATINUM = Path(__file__).parent.resolve()
VAULT_ROOT = PLATINUM.parent
AGENT_ID   = os.getenv("AGENT_ID", "unknown_agent")


def _run(cmd: list[str], cwd: Path = VAULT_ROOT, timeout: int = 60) -> tuple[bool, str]:
    """Run a git command. Returns (success, stdout)."""
    try:
        result = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            log.warning("git %s stderr: %s", cmd[1], result.stderr.strip())
            return False, result.stderr
        return True, result.stdout.strip()
    except subprocess.TimeoutExpired:
        log.error("git %s timed out after %ds", cmd[1], timeout)
        return False, "timeout"
    except Exception as e:
        log.error("git_sync error: %s", e)
        return False, str(e)


def sync_pull() -> bool:
    """
    Pull latest changes from remote before any read/write cycle.
    Uses --rebase --autostash so local uncommitted changes survive.
    Returns True if successful.
    """
    log.info("git pull --rebase --autostash")
    ok, out = _run(["git", "pull", "--rebase", "--autostash"])
    if ok:
        if "Already up to date" not in out:
            log.info("New changes pulled: %s", out[:120])
        else:
            log.info("Already up to date")
    return ok


def sync_push(message: str) -> bool:
    """
    Stage all platinum/ changes, commit with agent prefix, and push.
    Skips commit + push if nothing has changed.
    Returns True if successful (including skip).
    """
    # Stage only platinum/ directory — never touches other tiers' secrets
    _run(["git", "add", str(PLATINUM)])

    # Check if there's anything staged
    ok, status_out = _run(
        ["git", "status", "--porcelain", str(PLATINUM)], timeout=10
    )
    if not status_out.strip():
        log.info("Nothing to commit — skipping push")
        return True

    commit_msg = f"[{AGENT_ID}] {message}"
    ok, _ = _run(["git", "commit", "-m", commit_msg])
    if not ok:
        log.warning("git commit failed — may already be committed")

    ok, _ = _run(["git", "push"], timeout=90)
    if ok:
        log.info("git push OK: %s", commit_msg)
    else:
        log.warning("git push failed — will retry on next cycle")
    return ok


def has_uncommitted_changes() -> bool:
    """Return True if there are staged or unstaged changes in platinum/."""
    ok, out = _run(["git", "status", "--porcelain", str(PLATINUM)], timeout=10)
    return bool(out.strip())
