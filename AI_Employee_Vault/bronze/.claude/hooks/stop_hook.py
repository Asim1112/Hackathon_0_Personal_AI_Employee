"""
stop_hook.py — Ralph Wiggum Stop Hook for Claude Code
======================================================

Claude Code Stop hook that intercepts Claude's exit and re-injects
the task prompt if work remains, implementing the "Ralph Wiggum" loop.

How it fits in:
    1. User starts Claude Code (interactive session)
    2. ralph_loop.sh (or manually) writes .ralph_state.json with task details
    3. Claude processes the task and tries to exit
    4. THIS hook fires → reads state → checks completion → blocks or allows
    5. If blocked: Claude gets the reason as its next prompt and continues
    6. Repeat until done or max iterations

Hook input (from Claude Code via stdin):
    {
        "session_id":           "...",
        "transcript_path":      "~/.claude/projects/.../session.jsonl",
        "cwd":                  "/path/to/vault",
        "hook_event_name":      "Stop",
        "stop_hook_active":     false,   ← true if hook already triggered this cycle
        "last_assistant_message": "Claude's final response text"
    }

Hook output (stdout, exit code 0):
    Allow exit:  (no output, or omit "decision" field)
    Block exit:  {"decision": "block", "reason": "<re-injected prompt>"}

Exit codes:
    0  →  honour the JSON output (block if decision=block, else allow)
    2  →  blocking error — stderr text fed back to Claude

Docs: https://docs.anthropic.com/en/docs/claude-code/hooks
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── Read hook input ────────────────────────────────────────────────────────────

try:
    raw = sys.stdin.read()
    hook_input: dict = json.loads(raw)
except (json.JSONDecodeError, ValueError) as e:
    # Can't parse input → let Claude exit normally
    print(f"[stop_hook] Failed to parse hook input: {e}", file=sys.stderr)
    sys.exit(0)


# ── Extract fields ─────────────────────────────────────────────────────────────

cwd                  = Path(hook_input.get("cwd", "."))
stop_hook_active     = hook_input.get("stop_hook_active", False)
last_message         = hook_input.get("last_assistant_message", "")
session_id           = hook_input.get("session_id", "unknown")

state_path = cwd / ".ralph_state.json"


# ── Guard: no active Ralph loop ────────────────────────────────────────────────

if not state_path.exists():
    # No state file = no active Ralph loop. Let Claude exit normally.
    sys.exit(0)


# ── Load state ─────────────────────────────────────────────────────────────────

try:
    state: dict = json.loads(state_path.read_text(encoding="utf-8"))
except (json.JSONDecodeError, OSError) as e:
    print(f"[stop_hook] Could not read state file: {e}", file=sys.stderr)
    sys.exit(0)

task_id            = state.get("task_id", "unknown")
prompt             = state.get("prompt", "")
completion_promise = state.get("completion_promise", "TASK_COMPLETE")
max_iterations     = state.get("max_iterations", 5)
current_iteration  = state.get("current_iteration", 0)
vault_path         = Path(state.get("vault_path", str(cwd)))

timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")


# ── Completion check 1: Promise in Claude's last message ───────────────────────

if completion_promise and completion_promise in last_message:
    _msg = (
        f"[stop_hook {timestamp}] ✅ Completion promise '{completion_promise}' "
        f"found in response. Task {task_id} complete after {current_iteration} iteration(s)."
    )
    print(_msg, file=sys.stderr)
    state_path.unlink(missing_ok=True)
    sys.exit(0)


# ── Completion check 2: Needs_Action/ folder is empty ─────────────────────────

needs_action = vault_path / "Needs_Action"
try:
    pending_files = [
        f for f in needs_action.iterdir()
        if f.suffix == ".md" and f.name != ".gitkeep"
    ]
except OSError:
    pending_files = []

if not pending_files:
    _msg = (
        f"[stop_hook {timestamp}] ✅ Needs_Action/ is empty. "
        f"Task {task_id} complete after {current_iteration} iteration(s)."
    )
    print(_msg, file=sys.stderr)
    state_path.unlink(missing_ok=True)
    sys.exit(0)


# ── Completion check 3: Max iterations reached ────────────────────────────────

if current_iteration >= max_iterations:
    _msg = (
        f"[stop_hook {timestamp}] ⚠️  Max iterations ({max_iterations}) reached "
        f"for task {task_id}. {len(pending_files)} file(s) still pending. "
        f"Allowing Claude to exit."
    )
    print(_msg, file=sys.stderr)
    state_path.unlink(missing_ok=True)
    sys.exit(0)


# ── Guard: stop_hook_active safety valve ──────────────────────────────────────
#
# stop_hook_active=True means Claude is ALREADY in a continuation triggered
# by a previous stop hook firing. If we've somehow not caught completion yet
# and we're in this state, allow exit to prevent runaway loops.
# This is a safety net — our iteration counter is the primary guard.

if stop_hook_active and current_iteration >= 2:
    _msg = (
        f"[stop_hook {timestamp}] ⚠️  stop_hook_active=True at iteration "
        f"{current_iteration}. Safety valve triggered. Allowing exit."
    )
    print(_msg, file=sys.stderr)
    state_path.unlink(missing_ok=True)
    sys.exit(0)


# ── Not done — increment and re-inject ────────────────────────────────────────

next_iteration = current_iteration + 1
state["current_iteration"] = next_iteration
state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

pending_names = "\n".join(f"  - {f.name}" for f in pending_files[:5])
if len(pending_files) > 5:
    pending_names += f"\n  ... and {len(pending_files) - 5} more"

reason = f"""\
[Ralph Wiggum Loop — Iteration {next_iteration}/{max_iterations}]

Needs_Action/ still has {len(pending_files)} unprocessed file(s):
{pending_names}

{prompt}

Continue processing until Needs_Action/ is completely empty.
Write {completion_promise} on the last line of your response when done."""

print(
    f"[stop_hook {timestamp}] ↻ Re-injecting prompt "
    f"(iteration {next_iteration}/{max_iterations}, "
    f"{len(pending_files)} file(s) remaining)",
    file=sys.stderr,
)

# Output the block decision to stdout for Claude Code to consume
print(json.dumps({"decision": "block", "reason": reason}))
sys.exit(0)
