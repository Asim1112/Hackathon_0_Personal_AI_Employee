"""
stop_hook.py — Advanced Ralph Wiggum Stop Hook (Gold Tier)
===========================================================

Intercepts Claude Code's exit signal and re-injects the task prompt if work
remains — implementing the autonomous "Ralph Wiggum" loop.

Gold-tier upgrade over Silver: **file-movement detection**.
Instead of only checking Needs_Action/ emptiness, this hook:

  1. Snapshots Needs_Action/ + Pending_Approval/ at the END of each iteration
  2. On next stop, DIFFS current state vs. snapshot to detect real progress
  3. If no files moved for 2+ consecutive iterations → STALL detected → exit
  4. If files moved to Pending_Approval/ → counts as progress (Claude drafted work)
  5. Reports which files were processed, what remains, and what was drafted

State file: .ralph_state.json (written by ralph_loop.sh or orchestrator)
Progress snapshot: .ralph_snapshot.json (written by THIS hook between iterations)

Hook input  (Claude Code → stdin, JSON):
    session_id, transcript_path, cwd, hook_event_name,
    stop_hook_active, last_assistant_message

Hook output (stdout, exit code 0):
    Allow exit:  {} or empty
    Block exit:  {"decision": "block", "reason": "<re-injected prompt>"}

Docs: https://docs.anthropic.com/en/docs/claude-code/hooks
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── Constants ─────────────────────────────────────────────────────────────────

COMPLETION_SIGNALS = [
    "TASK_COMPLETE",
    "task_complete",
    "Task complete",
    "All tasks complete",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _md_files(folder: Path) -> set[str]:
    """Return a set of .md filenames in a folder (empty set if folder missing)."""
    try:
        return {
            f.name for f in folder.iterdir()
            if f.suffix == ".md" and f.name != ".gitkeep"
        }
    except OSError:
        return set()


def _allow_exit(reason: str = "") -> None:
    if reason:
        print(f"[stop_hook {_now()}] {reason}", file=sys.stderr)
    sys.exit(0)


def _block_exit(reason: str, message: str) -> None:
    print(f"[stop_hook {_now()}] {message}", file=sys.stderr)
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


# ── Read hook input ────────────────────────────────────────────────────────────

try:
    hook_input: dict = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError) as exc:
    print(f"[stop_hook] Failed to parse hook input: {exc}", file=sys.stderr)
    sys.exit(0)

cwd              = Path(hook_input.get("cwd", "."))
stop_hook_active = hook_input.get("stop_hook_active", False)
last_message     = hook_input.get("last_assistant_message", "")
session_id       = hook_input.get("session_id", "unknown")

state_path    = cwd / ".ralph_state.json"
snapshot_path = cwd / ".ralph_snapshot.json"


# ── Guard: no active Ralph loop ────────────────────────────────────────────────

if not state_path.exists():
    sys.exit(0)


# ── Load state ─────────────────────────────────────────────────────────────────

try:
    state: dict = json.loads(state_path.read_text(encoding="utf-8"))
except (json.JSONDecodeError, OSError) as exc:
    print(f"[stop_hook] Could not read state file: {exc}", file=sys.stderr)
    sys.exit(0)

task_id            = state.get("task_id", "unknown")
prompt             = state.get("prompt", "")
completion_promise = state.get("completion_promise", "TASK_COMPLETE")
max_iterations     = state.get("max_iterations", 8)
current_iteration  = state.get("current_iteration", 0)
max_stall_iters    = state.get("max_stall_iterations", 2)
vault_path         = Path(state.get("vault_path", str(cwd)))

needs_action_dir   = vault_path / "Needs_Action"
pending_appr_dir   = vault_path / "Pending_Approval"


# ── Check 1: Explicit completion signal in Claude's last message ───────────────

all_signals = COMPLETION_SIGNALS + ([completion_promise] if completion_promise else [])
if any(sig in last_message for sig in all_signals if sig):
    _allow_exit(
        f"✅ Completion signal found in response. "
        f"Task {task_id} complete after {current_iteration} iteration(s)."
    )


# ── Current state snapshot ─────────────────────────────────────────────────────

current_needs_action  = _md_files(needs_action_dir)
current_pending_appr  = _md_files(pending_appr_dir)


# ── Check 2: Needs_Action/ is empty ───────────────────────────────────────────

if not current_needs_action:
    snapshot_path.unlink(missing_ok=True)
    _allow_exit(
        f"✅ Needs_Action/ is empty. "
        f"Task {task_id} complete after {current_iteration} iteration(s). "
        f"{len(current_pending_appr)} item(s) in Pending_Approval/ awaiting human review."
    )


# ── Check 3: Max iterations reached ───────────────────────────────────────────

if current_iteration >= max_iterations:
    snapshot_path.unlink(missing_ok=True)
    state_path.unlink(missing_ok=True)
    _allow_exit(
        f"⚠️  Max iterations ({max_iterations}) reached for task {task_id}. "
        f"{len(current_needs_action)} file(s) still in Needs_Action/. "
        f"Allowing Claude to exit."
    )


# ── Load previous snapshot (for diff) ─────────────────────────────────────────

prev_snapshot: dict = {}
if snapshot_path.exists():
    try:
        prev_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass

prev_needs_action = set(prev_snapshot.get("needs_action", []))
prev_pending_appr = set(prev_snapshot.get("pending_approval", []))
prev_stall_count  = prev_snapshot.get("stall_count", 0)


# ── Check 4: Stall detection (file-movement analysis) ─────────────────────────
#
# Progress is defined as ANY of:
#   a) Files disappeared from Needs_Action/ (moved to Done/ or elsewhere)
#   b) New files appeared in Pending_Approval/ (Claude drafted action files)
#
# If neither happened for max_stall_iters consecutive cycles → stall → exit.

if prev_needs_action:  # Only diff if we have a previous snapshot
    moved_out_of_queue = prev_needs_action - current_needs_action
    new_in_pending     = current_pending_appr - prev_pending_appr
    progress_made      = bool(moved_out_of_queue or new_in_pending)

    if not progress_made:
        stall_count = prev_stall_count + 1
        print(
            f"[stop_hook {_now()}] ⚠️  No file movement detected "
            f"(stall {stall_count}/{max_stall_iters}). "
            f"Needs_Action still has {len(current_needs_action)} file(s).",
            file=sys.stderr,
        )

        if stall_count >= max_stall_iters:
            snapshot_path.unlink(missing_ok=True)
            state_path.unlink(missing_ok=True)
            stalled_files = "\n".join(f"  - {f}" for f in sorted(current_needs_action)[:10])
            _allow_exit(
                f"🛑 Stall detected after {stall_count} iterations with no progress. "
                f"Exiting loop. Files still in Needs_Action/:\n{stalled_files}"
            )
    else:
        stall_count = 0  # Reset stall counter on any progress
        moved_names = sorted(moved_out_of_queue)[:5]
        new_names   = sorted(new_in_pending)[:5]
        print(
            f"[stop_hook {_now()}] ✓ Progress detected — "
            f"{len(moved_out_of_queue)} moved out of queue, "
            f"{len(new_in_pending)} new draft(s) in Pending_Approval/.",
            file=sys.stderr,
        )
        if moved_names:
            print(
                f"  Processed: {', '.join(moved_names)}"
                + (" ..." if len(moved_out_of_queue) > 5 else ""),
                file=sys.stderr,
            )
        if new_names:
            print(
                f"  Drafted:   {', '.join(new_names)}"
                + (" ..." if len(new_in_pending) > 5 else ""),
                file=sys.stderr,
            )
else:
    stall_count = 0  # First iteration — no snapshot to diff against


# ── Safety valve: stop_hook_active guard ──────────────────────────────────────
#
# stop_hook_active=True means we're already in a hook-triggered continuation.
# Combined with stall_count > 0 this is a reliable indicator of a runaway loop.

if stop_hook_active and stall_count > 0:
    snapshot_path.unlink(missing_ok=True)
    state_path.unlink(missing_ok=True)
    _allow_exit(
        f"⚠️  stop_hook_active=True with stall_count={stall_count}. "
        f"Safety valve triggered at iteration {current_iteration}. Allowing exit."
    )


# ── Write updated snapshot for NEXT iteration ─────────────────────────────────

next_iteration = current_iteration + 1
state["current_iteration"] = next_iteration
state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

snapshot_path.write_text(
    json.dumps({
        "iteration": next_iteration,
        "needs_action":    sorted(current_needs_action),
        "pending_approval": sorted(current_pending_appr),
        "stall_count":     stall_count,
        "timestamp":       datetime.now(timezone.utc).isoformat(),
    }, indent=2),
    encoding="utf-8",
)


# ── Build re-injection prompt ──────────────────────────────────────────────────

remaining_files = sorted(current_needs_action)
shown = remaining_files[:6]
overflow = len(remaining_files) - len(shown)

pending_list = "\n".join(f"  - {f}" for f in shown)
if overflow:
    pending_list += f"\n  ... and {overflow} more"

# Contextual hint based on what's remaining
file_types = {f.split("_")[0] for f in remaining_files}
type_hint = ""
if "EMAIL" in file_types:
    type_hint += "\n- Email items: use SKILL_Gmail_Triage"
if "WHATSAPP" in file_types:
    type_hint += "\n- WhatsApp items: use SKILL_WhatsApp_Triage"
if "LINKEDIN" in file_types:
    type_hint += "\n- LinkedIn items: use SKILL_LinkedIn_Draft"
if "TWITTER" in file_types:
    type_hint += "\n- Twitter items: use SKILL_Twitter_Draft"
if "FACEBOOK" in file_types or "INSTAGRAM" in file_types:
    type_hint += "\n- Facebook/Instagram items: use SKILL_Facebook_Instagram"
if "ODOO" in file_types:
    type_hint += "\n- Odoo alerts: use SKILL_Odoo_Accounting"

pending_summary = (
    f"{len(current_pending_appr)} item(s) already drafted in Pending_Approval/ — do not re-process those."
    if current_pending_appr else ""
)

reason = f"""\
[Ralph Wiggum — Iteration {next_iteration}/{max_iterations}]

Needs_Action/ still has {len(remaining_files)} unprocessed file(s):
{pending_list}
{type_hint}

{pending_summary}

{prompt}

For each remaining file:
1. Read the full file content
2. Apply the correct SKILL from skills/
3. Move it to Done/ when processed
4. Log the action to Logs/{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json

Write {completion_promise} on the last line when Needs_Action/ is completely empty.\
"""

_block_exit(
    reason,
    f"↻ Re-injecting prompt (iteration {next_iteration}/{max_iterations}, "
    f"{len(remaining_files)} file(s) remaining, stall_count={stall_count})",
)
