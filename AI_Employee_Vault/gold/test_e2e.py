"""
test_e2e.py — Silver AI Employee End-to-End Pipeline Test
==========================================================

Simulates the full pipeline for all three watcher types:

  Scenario 1 — WhatsApp (new contact, invoice keyword)
    whatsapp_watcher → WHATSAPP_*.md in Needs_Action/
    → SKILL_WhatsApp_Triage → new contact detected
    → SKILL_HITL_Approval → NEW_CONTACT_REVIEW_*.md in Pending_Approval/
    → source → Done/

  Scenario 2 — LinkedIn opportunity (business_opportunity category)
    linkedin_watcher → LINKEDIN_*.md in Needs_Action/
    → SKILL_Reasoning_Loop → PLAN_*.md in Plans/ → In_Progress/
    → SKILL_LinkedIn_Draft → LINKEDIN_DRAFT_*.md in Pending_Approval/
    → source → Done/

  Scenario 3 — Email from known contact (project status query)
    gmail_watcher → EMAIL_*.md in Needs_Action/
    → SKILL_Gmail_Triage → known contact, no HITL
    → DRAFT_REPLY_*.md in Inbox/
    → source → Done/

Usage:
    python test_e2e.py              Create fixtures + show expected pipeline
    python test_e2e.py --run        Create fixtures + invoke Claude cycle
    python test_e2e.py --check      Show current vault folder counts (no changes)
    python test_e2e.py --clean      Remove all test fixture files
"""

import argparse
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(__file__).parent.resolve()
NOW   = datetime.now(timezone.utc).isoformat()
DATE  = datetime.now().strftime("%Y-%m-%d")

CLAUDE_PROMPT = (
    "Read CLAUDE.md. Process all pending items in Needs_Action/ using the appropriate skills. "
    "Run SKILL_WhatsApp_Triage for type:whatsapp, SKILL_Gmail_Triage for type:email, "
    "SKILL_Reasoning_Loop for type:linkedin_opportunity. "
    "Use SKILL_HITL_Approval for any HITL triggers. "
    "Update Dashboard.md when done. Write TASK_COMPLETE on your last line."
)

# ---------------------------------------------------------------------------
# Test fixtures — one per watcher type
# ---------------------------------------------------------------------------

FIXTURES: dict[str, dict] = {

    "WHATSAPP_TEST_2026-02-25_John_Smith_test1234.md": {
        "folder": "Needs_Action",
        "content": f"""\
---
type: whatsapp
from: "John Smith"
keyword: invoice
received: "{NOW}"
priority: high
status: pending
source: whatsapp
---

# WhatsApp: John Smith

**From:** John Smith
**Keyword matched:** invoice
**Received:** {NOW}

---

## Message Content

Hi, just checking on the invoice you sent last week — can you confirm it's been received? Need to process ASAP, thanks.

---

## Suggested Actions

- [ ] Review this WhatsApp message
- [ ] Reply via WhatsApp (requires HITL if new contact)
- [ ] Log as business intelligence

---

## Processing Notes

> _(Claude: add your analysis and action taken here before moving to Done/)_

---

*Captured by WhatsAppWatcher at {NOW}*
""",
        "scenario": "WhatsApp → new contact + invoice keyword → HITL gate",
        "expected": [
            "SKILL_WhatsApp_Triage: reads file, detects 'John Smith' is NOT in Key Contacts",
            "→ SKILL_HITL_Approval (trigger #2: new contact)",
            "→ Pending_Approval/NEW_CONTACT_REVIEW_John_Smith_{DATE}.md written",
            "→ source file moved to Done/ with status: processed",
        ],
    },

    f"LINKEDIN_TEST_2026-02-25_Business_Proposal_test5678.md": {
        "folder": "Needs_Action",
        "content": f"""\
---
type: linkedin_opportunity
linkedin_id: "li_notif_test5678"
category: business_opportunity
link: "https://www.linkedin.com/messaging/"
received: "{NOW}"
priority: high
status: pending
source: linkedin
---

# LinkedIn: Business Opportunity

**Category:** business_opportunity
**Priority:** high
**Received:** {NOW}

---

## Notification Content

Jane Doe has sent you a message: "Hi, I came across your profile and I'm very interested in your consulting services. We have a project we'd like to discuss — would you be available for a call this week?"

---

## Suggested Actions

- [ ] Review this LinkedIn notification
- [ ] Reply via LinkedIn (requires HITL if new contact)
- [ ] Use SKILL_LinkedIn_Draft to draft a post about this opportunity
- [ ] Log as business intelligence
- [ ] Archive if no action needed (move to Done/)

---

## Processing Notes

> _(Claude: add your analysis and action taken here before moving to Done/)_

---

*Captured by LinkedInWatcher at {NOW}*
""",
        "scenario": "LinkedIn business_opportunity → Reasoning Loop → Plan → LinkedIn Draft → HITL",
        "expected": [
            f"SKILL_Reasoning_Loop: creates Plans/PLAN_LinkedIn_Consulting_Enquiry_{DATE}.md",
            "→ Plan moved to In_Progress/",
            "→ Step: draft DM reply → Pending_Approval/NEW_CONTACT_REVIEW_Jane_Doe_*.md",
            f"→ SKILL_LinkedIn_Draft → Pending_Approval/LINKEDIN_DRAFT_Consulting_Services_{DATE}.md",
            "→ source file moved to Done/ when plan complete",
        ],
    },

    f"EMAIL_TEST_2026-02-25_Project_Status_testabcd.md": {
        "folder": "Needs_Action",
        "content": f"""\
---
type: email
gmail_id: "test_email_abcd"
from: "Top Client <topclient@example.com>"
subject: "Project status update"
date_sent: "{NOW}"
priority: medium
status: pending
source: gmail
---

# Email: Project status update

**From:** Top Client <topclient@example.com>
**Subject:** Project status update
**Received:** {NOW}

---

## Email Body

Hi,

Just wanted to check in on the status of our current project. We have a board meeting next week and it would be helpful to have an update on progress to date.

Could you send over a quick summary when you get a chance?

Thanks,
Top Client

---

## Suggested Actions

- [ ] Review this email
- [ ] Draft a reply

---

## Processing Notes

> _(Claude: add your analysis and action taken here before moving to Done/)_

---

*Captured by GmailWatcher at {NOW}*
""",
        "scenario": "Email from known contact → Gmail Triage → Draft reply → Inbox/",
        "expected": [
            "SKILL_Gmail_Triage: reads file, 'Top Client' found in Company_Handbook Section 11 Key Contacts",
            "→ No HITL required (known contact, routine query, < £50)",
            f"→ Inbox/DRAFT_REPLY_Project_Status_Update_{DATE}.md written",
            "→ source file moved to Done/ with status: processed",
        ],
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def vault_state() -> dict[str, int]:
    """Count .md files in each key vault folder."""
    folders = ["Needs_Action", "Inbox", "Plans", "In_Progress",
               "Pending_Approval", "Approved", "Rejected", "Done"]
    return {f: len(list((VAULT / f).glob("*.md"))) for f in folders if (VAULT / f).exists()}


def print_state(label: str) -> None:
    state = vault_state()
    print(f"\n{'─' * 50}")
    print(f"  {label}")
    print(f"{'─' * 50}")
    for folder, count in state.items():
        bar   = "█" * count if count else "·"
        flag  = " ← pending" if folder == "Needs_Action" and count else ""
        flag  = " ← review!" if folder == "Pending_Approval" and count else flag
        print(f"  {folder:20s} {count:3d}  {bar}{flag}")
    print()


def create_fixtures() -> list[Path]:
    created = []
    for filename, spec in FIXTURES.items():
        dest = VAULT / spec["folder"] / filename
        dest.write_text(spec["content"], encoding="utf-8")
        print(f"  ✅ Created: {spec['folder']}/{filename}")
        created.append(dest)
    return created


def show_expected_pipeline() -> None:
    print("\n" + "═" * 60)
    print("  EXPECTED PIPELINE (Silver Tier End-to-End)")
    print("═" * 60)
    for i, (filename, spec) in enumerate(FIXTURES.items(), 1):
        print(f"\n  Scenario {i}: {spec['scenario']}")
        print(f"  Source: Needs_Action/{filename}")
        for step in spec["expected"]:
            print(f"    {step}")
    print()


def clean_fixtures() -> None:
    removed = 0
    for filename in FIXTURES:
        for folder in ["Needs_Action", "Done", "Plans", "In_Progress"]:
            p = VAULT / folder / filename
            if p.exists():
                p.unlink()
                print(f"  🗑  Removed: {folder}/{filename}")
                removed += 1
    print(f"\n  Cleaned {removed} fixture file(s).")


def _find_claude() -> list[str]:
    """
    Locate the claude CLI on the current platform.
    On Windows, npm wraps the binary as claude.cmd — try that first.
    Falls back to plain 'claude' (works on macOS/Linux).
    """
    if platform.system() == "Windows":
        for candidate in ("claude.cmd", "claude"):
            if shutil.which(candidate):
                return [candidate]
        # Last resort: let the shell resolve it
        return ["claude.cmd"]
    return ["claude"]


def run_claude_cycle() -> None:
    print("\n  Running Claude processing cycle…")
    print(f"  Prompt: {CLAUDE_PROMPT[:80]}…\n")
    cmd = _find_claude() + ["--print", CLAUDE_PROMPT]
    try:
        subprocess.run(
            cmd,
            cwd=str(VAULT),
            timeout=600,
            check=False,
            shell=(platform.system() == "Windows"),  # needed for .cmd files on Windows
        )
    except FileNotFoundError:
        print("  ERROR: 'claude' / 'claude.cmd' not found.")
        print("  Install Claude Code: https://claude.ai/download")
        print("  Then re-open this terminal so PATH is refreshed.")
    except subprocess.TimeoutExpired:
        print("  ERROR: Claude cycle timed out after 10 minutes.")


def check_outputs() -> None:
    """Check which expected output files were actually created."""
    print("\n  Output file check:")
    expected_patterns = [
        ("Pending_Approval", "NEW_CONTACT_REVIEW_*John*"),
        ("Pending_Approval", "LINKEDIN_DRAFT_*"),
        ("Inbox",            "DRAFT_REPLY_*Project*"),
        ("Plans",            "PLAN_*LinkedIn*"),
        ("Done",             "WHATSAPP_TEST_*"),
        ("Done",             "LINKEDIN_TEST_*"),
        ("Done",             "EMAIL_TEST_*"),
    ]
    all_ok = True
    for folder, pattern in expected_patterns:
        matches = list((VAULT / folder).glob(pattern))
        status  = "✅" if matches else "❌ NOT FOUND"
        fname   = matches[0].name if matches else "—"
        print(f"  {status}  {folder}/{pattern:30s}  → {fname}")
        if not matches:
            all_ok = False
    print()
    if all_ok:
        print("  All expected outputs present — pipeline test PASSED")
    else:
        print("  Some outputs missing — run with --run to process, or check Claude logs")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Silver AI Employee E2E Pipeline Test")
    parser.add_argument("--run",   action="store_true", help="Create fixtures + run Claude cycle")
    parser.add_argument("--check", action="store_true", help="Show vault state without changes")
    parser.add_argument("--clean", action="store_true", help="Remove fixture files")
    args = parser.parse_args()

    print("\n" + "═" * 60)
    print("  Silver AI Employee — End-to-End Pipeline Test")
    print("═" * 60)
    print(f"  Vault: {VAULT}\n")

    if args.check:
        print_state("Current Vault State")
        check_outputs()
        return

    if args.clean:
        clean_fixtures()
        return

    # Default + --run: create fixtures, show expected, optionally run Claude
    print("  Creating test fixture files in Needs_Action/…")
    create_fixtures()
    print_state("Vault State BEFORE processing")
    show_expected_pipeline()

    if args.run:
        run_claude_cycle()
        print_state("Vault State AFTER processing")
        check_outputs()
    else:
        print("  ─────────────────────────────────────────────────────")
        print("  Fixtures created. To run Claude processing cycle:")
        print("    python test_e2e.py --run")
        print()
        print("  To check outputs after running:")
        print("    python test_e2e.py --check")
        print()
        print("  To remove fixtures:")
        print("    python test_e2e.py --clean")
        print("  ─────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
