#!/usr/bin/env bash
# =============================================================================
# ralph_loop.sh — Ralph Wiggum Autonomous Loop Launcher
# =============================================================================
#
# Starts a Claude Code loop that re-injects the task prompt after each
# response until Needs_Action/ is empty OR the completion promise appears
# in Claude's output OR max iterations is reached.
#
# Architecture:
#   This script handles the shell-level loop (reliable, works with -p mode).
#   .claude/hooks/stop_hook.py handles the native Claude Code Stop hook
#   (for interactive sessions — same logic, different trigger mechanism).
#
# Usage:
#   bash ralph_loop.sh
#   bash ralph_loop.sh "Custom prompt here"
#   bash ralph_loop.sh "Process Needs_Action" --max-iterations 10
#   bash ralph_loop.sh "Process Needs_Action" --completion-promise "ALL_DONE"
#
# =============================================================================
set -euo pipefail

# ── Resolve vault root (directory containing this script) ──────────────────────
# pwd -W returns Windows-style path (e.g. F:/path) which Python on Windows needs.
# Falls back to regular pwd on Linux/macOS where -W is not available.
VAULT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -W 2>/dev/null || pwd)"

# ── Defaults ───────────────────────────────────────────────────────────────────
DEFAULT_PROMPT="Read CLAUDE.md for vault operating instructions. \
Then use SKILL_Process_Needs_Action from skills/SKILL_Process_Needs_Action.md \
to process all files in Needs_Action/. Read Company_Handbook.md first. \
For each file: write Processing Notes, update status to processed, move to Done/. \
Update Dashboard.md when all files are processed. \
Write TASK_COMPLETE on the last line of your response when Needs_Action/ is fully empty."

MAX_ITERATIONS=5
COMPLETION_PROMISE="TASK_COMPLETE"

# ── Argument parsing ───────────────────────────────────────────────────────────
# If first arg doesn't start with --, treat it as the prompt
if [[ $# -gt 0 && "$1" != --* ]]; then
    PROMPT="$1"
    shift
else
    PROMPT="$DEFAULT_PROMPT"
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --max-iterations|-n)
            MAX_ITERATIONS="$2"; shift 2 ;;
        --completion-promise|-p)
            COMPLETION_PROMISE="$2"; shift 2 ;;
        --help|-h)
            sed -n '2,25p' "$0" | tr -d '#'
            exit 0 ;;
        *)
            echo "[Ralph] Unknown argument: $1" >&2; exit 1 ;;
    esac
done

# ── Helpers ────────────────────────────────────────────────────────────────────
PYTHON="${PYTHON:-python}"
STATE_FILE="$VAULT_DIR/.ralph_state.json"
NEEDS_ACTION="$VAULT_DIR/Needs_Action"
DONE_DIR="$VAULT_DIR/Done"

# Use Python for reliable JSON (handles quotes/special chars in prompt)
write_state() {
    local iteration="$1"
    "$PYTHON" - <<PYEOF
import json
from pathlib import Path

state = {
    "task_id":            "$TASK_ID",
    "prompt":             """$PROMPT""",
    "completion_promise": "$COMPLETION_PROMISE",
    "max_iterations":     $MAX_ITERATIONS,
    "current_iteration":  $iteration,
    "vault_path":         "$VAULT_DIR",
    "started_at":         "$STARTED_AT",
}
Path("$STATE_FILE").write_text(json.dumps(state, indent=2))
PYEOF
}

count_pending() {
    # Count .md files in Needs_Action/ excluding .gitkeep
    find "$NEEDS_ACTION" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' '
}

count_done() {
    find "$DONE_DIR" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' '
}

# ── Pre-flight checks ──────────────────────────────────────────────────────────
if ! command -v claude &>/dev/null; then
    echo ""
    echo "[Ralph] ✗ ERROR: 'claude' command not found in PATH."
    echo "        Install Claude Code: https://claude.ai/code"
    echo "        Then ensure it is in your PATH."
    exit 1
fi

if ! command -v "$PYTHON" &>/dev/null; then
    # Fallback to python3
    if command -v python3 &>/dev/null; then
        PYTHON="python3"
    else
        echo "[Ralph] ✗ ERROR: python / python3 not found." >&2; exit 1
    fi
fi

# ── Initialise ─────────────────────────────────────────────────────────────────
TASK_ID="ralph_$(date +%Y%m%d_%H%M%S)"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

write_state 0

# ── Banner ─────────────────────────────────────────────────────────────────────
echo ""
echo "┌──────────────────────────────────────────────────────┐"
echo "│           Ralph Wiggum — Autonomous Loop             │"
echo "│           Bronze Tier AI Employee                    │"
echo "└──────────────────────────────────────────────────────┘"
echo ""
echo "  Task ID       : $TASK_ID"
echo "  Max iterations: $MAX_ITERATIONS"
echo "  Promise string: $COMPLETION_PROMISE"
echo "  Vault         : $VAULT_DIR"
echo "  State file    : $STATE_FILE"
echo ""
echo "  Prompt:"
echo "  $(echo "$PROMPT" | head -c 120)..."
echo ""
PENDING_START=$(count_pending)
echo "  Files in Needs_Action/ at start: $PENDING_START"
echo ""
echo "──────────────────────────────────────────────────────────"

# ── Main loop ─────────────────────────────────────────────────────────────────
ITERATION=0
DONE_REASON=""

for ITERATION in $(seq 1 "$MAX_ITERATIONS"); do

    echo ""
    echo "┌─ Iteration $ITERATION / $MAX_ITERATIONS ────────────────────────────────────"

    PENDING=$(count_pending)

    # Build the prompt for this iteration
    if [[ $ITERATION -eq 1 ]]; then
        CURRENT_PROMPT="$PROMPT"
    else
        CURRENT_PROMPT="[Ralph Wiggum Loop — Iteration ${ITERATION}/${MAX_ITERATIONS}]

Needs_Action/ still has ${PENDING} unprocessed file(s).

$PROMPT

Continue until every file is moved to Done/. Write $COMPLETION_PROMISE on the last line when Needs_Action/ is completely empty."
    fi

    echo "│  Pending files : $PENDING"
    echo "│  Running Claude..."
    echo "└──────────────────────────────────────────────────────────"
    echo ""

    # Update iteration count in state file
    write_state "$ITERATION"

    # ── Run Claude ──────────────────────────────────────────────────────────────
    # Unset CLAUDECODE so this works whether called from inside or outside a
    # Claude Code session. (Nested sessions are blocked by default.)
    CLAUDE_OUTPUT=""
    CLAUDE_OUTPUT=$(unset CLAUDECODE && claude --print "$CURRENT_PROMPT" 2>&1) || true
    echo "$CLAUDE_OUTPUT"

    # ── Completion checks ───────────────────────────────────────────────────────

    # Check 1: Completion promise found in Claude's output
    if echo "$CLAUDE_OUTPUT" | grep -qF "$COMPLETION_PROMISE" 2>/dev/null; then
        DONE_REASON="completion_promise"
        echo ""
        echo "  ✅ Completion promise '$COMPLETION_PROMISE' detected in Claude's response."
        break
    fi

    # Check 2: Needs_Action/ is empty
    PENDING_AFTER=$(count_pending)
    if [[ "$PENDING_AFTER" -eq 0 ]]; then
        DONE_REASON="queue_empty"
        echo ""
        echo "  ✅ Needs_Action/ is empty — all files processed."
        break
    fi

    # Not done — log and continue
    echo ""
    echo "  ↻ Iteration $ITERATION complete. $PENDING_AFTER file(s) still pending."

    # Final iteration — no more loops
    if [[ $ITERATION -eq $MAX_ITERATIONS ]]; then
        DONE_REASON="max_iterations"
    fi

done

# ── Final report ───────────────────────────────────────────────────────────────
echo ""
echo "──────────────────────────────────────────────────────────"
echo "  Ralph Wiggum Loop — Final Report"
echo "──────────────────────────────────────────────────────────"
echo "  Task ID        : $TASK_ID"
echo "  Iterations used: $ITERATION / $MAX_ITERATIONS"
echo "  Exit reason    : ${DONE_REASON:-incomplete}"
echo "  Files in Done/ : $(count_done)"
echo "  Still pending  : $(count_pending)"
echo ""

case "$DONE_REASON" in
    completion_promise)
        echo "  ✅ SUCCESS — Claude confirmed task complete ('$COMPLETION_PROMISE')." ;;
    queue_empty)
        echo "  ✅ SUCCESS — Needs_Action/ is empty." ;;
    max_iterations)
        echo "  ⚠️  MAX ITERATIONS reached ($MAX_ITERATIONS). Check remaining files manually." ;;
    *)
        echo "  ⚠️  Loop exited without clear completion signal." ;;
esac

# Cleanup state file
rm -f "$STATE_FILE"
echo "  State file cleaned up."
echo ""
