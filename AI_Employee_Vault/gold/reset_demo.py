"""
reset_demo.py — Gold Tier Demo Reset Script

Resets the vault to a clean, fully staged demo-ready state in one command.
Run this between every demo recording attempt.

Usage:
    uv run python reset_demo.py

What it does:
    1. Creates all required folders if missing (Pending_Approval/, etc.)
    2. Clears Needs_Action/, Inbox/, Pending_Approval/, Approved/ to empty
    3. Archives cleared files to Archive/ (nothing deleted)
    4. Writes 5 fresh demo source files to Needs_Action/
    5. Resets Dashboard.md to pre-processing state
    6. Prints a final readiness checklist

It does NOT:
    - Touch Done/ (keep full history)
    - Touch Logs/ (keep audit trail)
    - Touch Briefings/ (keep CEO briefing if already generated)
    - Start MCP servers or orchestrator (you do that separately)
"""

import io
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1252 emoji crash)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VAULT = Path(__file__).parent.resolve()
NOW = datetime.now().astimezone()
TODAY = NOW.strftime("%Y-%m-%d")
NOW_ISO = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")

# ── Folders that must exist ────────────────────────────────────────────────────

REQUIRED_FOLDERS = [
    "Needs_Action",
    "Done",
    "Inbox",
    "Pending_Approval",
    "Approved",
    "Rejected",
    "Plans",
    "In_Progress",
    "Archive",
    "Briefings",
    "Accounting",
    "Social_Analytics",
    "Logs",
    "skills",
    "mcp_servers",
]

# ── Folders to clear before staging ───────────────────────────────────────────

CLEAR_FOLDERS = [
    "Needs_Action",
    "Inbox",
    "Pending_Approval",
    "Approved",
]

# ── Demo source files ──────────────────────────────────────────────────────────

DEMO_FILES = {

    f"NEEDS_ACTION/EMAIL_{TODAY}_AI_Project_Milestone_demo01.md": f"""\
---
type: email
status: pending
platform: gmail
from_name: "Sarah Johnson"
from_email: "sarah.johnson@techcorp.com"
from: "Sarah Johnson <sarah.johnson@techcorp.com>"
to: "asimhussain787@gmail.com"
subject: "Q2 AI Integration Project — Milestone Update Request"
received: {TODAY}T08:05:00Z
message_id: "<techcorp-{TODAY}-q2-milestone-001@gmail.com>"
thread_id: "techcorp-ai-integration-q2"
is_new_contact: false
priority: high
logged: false
---

# Email — Q2 AI Integration Project Milestone Update Request

**From:** Sarah Johnson <sarah.johnson@techcorp.com>
**To:** asimhussain787@gmail.com
**Subject:** Q2 AI Integration Project — Milestone Update Request
**Received:** {TODAY} 08:05 UTC

---

## Email Body

Hi,

Hope you're well. Just following up on the AI integration project — we're heading into end-of-quarter reviews next week and the board has asked for an update on where things stand.

Specifically, we need to know:

1. Is the email triage automation live and processing production traffic?
2. Has the LinkedIn lead pipeline been connected to the CRM?
3. What's the current status on the Odoo invoicing module — are we on track for the April go-live?

Could you send over a brief status summary by Friday? Nothing formal — just a paragraph or two on each point so we can present it to the board.

Also, are we still on for the demo call next Tuesday at 2pm?

Thanks,
Sarah

---

## Action Required

Use SKILL_Gmail_Triage to classify and draft a reply. Existing client — reply authorised without new-contact HITL. Draft reply required covering all 3 project status points. Confirm Tuesday demo call.
""",

    f"NEEDS_ACTION/LINKEDIN_{TODAY}_enterprise_automation_enquiry_demo02.md": f"""\
---
type: linkedin_opportunity
status: pending
platform: linkedin
from_name: "Marcus Webb"
from_title: "Chief Operating Officer"
from_company: "Apex Advisory Partners"
from_profile: "linkedin.com/in/marcus-webb-apex"
is_new_contact: true
estimated_value: high
priority: high
received: {TODAY}T08:10:00Z
logged: false
---

# LinkedIn Opportunity — Marcus Webb, COO · Apex Advisory Partners

**Channel:** LinkedIn Direct Message
**Received:** {TODAY} 08:10 UTC
**New contact:** YES — HITL required before any reply

---

## Their Message

Hi,

I've been following your AI automation work for a while and finally decided to reach out. I'm COO at Apex Advisory Partners — 45 people, professional services, mostly advisory work for financial services clients.

We're drowning in operational overhead. Three things are killing us:
1. Email triage and client communications — probably 2–3 hours per person per day
2. Invoice management — we're always chasing overdue payments manually
3. Drafting thought leadership content — it just doesn't get done

Your Human-in-the-Loop approach is exactly what I'd need to get sign-off internally. Pure automation is a non-starter for our clients, but AI-assisted with oversight? That's a conversation I can have.

Would love to jump on a discovery call. I'm free most mornings next week.

Marcus

---

## Action Required

Use SKILL_LinkedIn_Draft:
1. Draft LinkedIn thought leadership post triggered by this enquiry → write to Pending_Approval/
2. Escalate NEW_CONTACT_REVIEW to Pending_Approval/ — no reply until human approves
3. Move source file to Done/
""",

    f"NEEDS_ACTION/TWITTER_{TODAY}_post_request_demo03.md": f"""\
---
type: twitter
status: pending
platform: twitter
twitter_type: post_request
source: admin_task
topic: "AI Employee system capabilities — professional services automation"
tone: professional
max_chars: 280
include_hashtags: true
received: {TODAY}T08:15:00Z
priority: normal
logged: false
---

# Twitter Post Request — AI Employee Capabilities

**Type:** Admin task — standalone post (NOT a reply to anyone)
**Source:** Scheduled content batch
**Received:** {TODAY} 08:15 UTC

---

## Brief

Write a single standalone tweet (max 280 characters) about the Gold Tier AI Employee system.

**Key message to convey:**
The system monitors 5 live channels (Email, LinkedIn, Twitter, Facebook, Odoo) simultaneously, drafts all responses, and executes only after human approval — demonstrating autonomous AI operations for professional services businesses.

**Tone:** Professional, confident, specific — no generic hype.

**Constraints:**
- Standalone tweet — NOT a reply to any existing tweet
- Must be under 280 characters (count carefully)
- Include 2–3 relevant hashtags at the end
- No clickbait, no filler phrases like "Excited to announce"

**Target audience:** Business owners, operations leads, fintech professionals

---

## Action Required

Use SKILL_Twitter_Draft to draft a single tweet and write to `Pending_Approval/` with correct frontmatter:
- `type: social_draft`
- `send_via_mcp: twitter-mcp`
- `action: post_tweet`

Include Action Data JSON block with `"action": "post_tweet"` and `"content"` fields.
""",

    f"NEEDS_ACTION/FACEBOOK_{TODAY}_post_request_demo04.md": f"""\
---
type: facebook
status: pending
platform: facebook
facebook_type: post_request
source: admin_task
topic: "Personal AI Employee system — business announcement for professional services audience"
tone: professional
received: {TODAY}T08:20:00Z
priority: normal
logged: false
---

# Facebook Post Request — Business Announcement

**Type:** Admin task — Facebook Business Page post
**Source:** Scheduled content batch
**Received:** {TODAY} 08:20 UTC

---

## Brief

Write a Facebook Business Page post announcing the Gold Tier Personal AI Employee system.

**Key messages to convey:**
1. The system monitors Email, LinkedIn, Twitter, Facebook, and Odoo ERP simultaneously
2. Every outbound action (email send, social post, invoice creation) requires explicit human approval before execution
3. Full audit trail on every action — nothing happens without a record
4. Designed for professional services businesses and consultancies

**Tone:** Professional, authoritative, accessible — written for business owners and operations managers, not developers.

**Format:** 2–4 paragraphs. End with a question or call-to-action to encourage engagement.

**Constraints:**
- No emojis unless they add genuine value
- No generic phrases like "We're thrilled to share"
- Specific and concrete — mention actual capabilities, not vague promises
- Do NOT include any URLs

---

## Action Required

Use SKILL_Facebook_Instagram to draft a Facebook post and write to `Pending_Approval/` with exact frontmatter:
- `type: social_post`
- `send_via_mcp: facebook-instagram-mcp`
- `action: post_facebook`

Include Action Data JSON block with `"message"` field containing the full post text.
""",

    f"NEEDS_ACTION/INSTAGRAM_{TODAY}_post_request_demo05.md": f"""\
---
type: instagram
status: pending
platform: instagram
instagram_type: post_request
source: admin_task
topic: "Personal AI Employee system — visual announcement for Instagram audience"
tone: professional
image_url: https://i.postimg.cc/Hnm43D2q/Gemini-Generated-Image-w0ch6pw0ch6pw0ch.png
received: {TODAY}T08:30:00Z
priority: normal
logged: false
---

# Instagram Post Request — AI Employee Visual Announcement

**Type:** Admin task — Instagram Business account post
**Source:** Scheduled content batch
**Received:** {TODAY} 08:30 UTC

---

## Brief

Write an Instagram post caption to accompany the provided image announcing the Gold Tier Personal AI Employee system.

**Image URL (mandatory — do not change):**
https://i.postimg.cc/Hnm43D2q/Gemini-Generated-Image-w0ch6pw0ch6pw0ch.png

**Key messages:**
1. AI Employee monitors Email, LinkedIn, Twitter, Facebook, and Odoo simultaneously
2. Every action requires human approval before execution — full HITL control
3. Built for professional services businesses

**Tone:** Professional, concise, Instagram-appropriate
**Format:** 3–5 sentences + 5–8 relevant hashtags on a new line
**Constraints:** No generic openers like "Excited to share", keep it under 300 words

---

## Action Required

Use SKILL_Facebook_Instagram to draft an Instagram post and write to `Pending_Approval/` with exact frontmatter:
- `type: social_post`
- `platform: instagram`
- `send_via_mcp: facebook-instagram-mcp`
- `action: post_instagram`
- `image_url: https://i.postimg.cc/Hnm43D2q/Gemini-Generated-Image-w0ch6pw0ch6pw0ch.png`

Include Action Data JSON block with BOTH `"caption"` AND `"image_url"` fields. The image_url MUST be:
https://i.postimg.cc/Hnm43D2q/Gemini-Generated-Image-w0ch6pw0ch6pw0ch.png
""",

    f"NEEDS_ACTION/ODOO_{TODAY}_overdue_invoice_INV-2026-010.md": f"""\
---
type: odoo_alert
status: pending
platform: odoo
action_hint: create_invoice
partner: "Meridian Consulting Group"
invoice_ref: "INV-2026-010"
amount_due: 2400.00
currency: GBP
overdue_days: 31
received: {TODAY}T08:25:00Z
priority: high
logged: false
contact_email: asimhussain8000@gmail.com
---

# Odoo Alert — Overdue Invoice INV-2026-010

**Type:** Odoo accounting alert — overdue invoice
**Partner:** Meridian Consulting Group
**Invoice:** INV-2026-010
**Amount:** £2,400.00
**Overdue by:** 31 days
**Received:** {TODAY} 08:25 UTC

---

## Alert Details

Odoo ERP has flagged invoice INV-2026-010 issued to Meridian Consulting Group as overdue by 31 days.

**Invoice Line:**
- Service: AI Strategy Consulting — February 2026
- Quantity: 1
- Unit price: £2,400.00
- Total: £2,400.00

**Payment terms:** Net 30 days
**Due date:** 2026-02-24
**Last payment received:** None

---

## Action Required

Use SKILL_Odoo_Accounting to create an invoice in Odoo and write an ODOO_REVIEW file to `Pending_Approval/` with exact frontmatter:
- `type: odoo_action`
- `send_via_mcp: odoo-mcp`
- `action: create_invoice`

And include Action Data JSON block with fields:
- `partner_name`: "Meridian Consulting Group"
- `lines`: array with `name`, `quantity`, `price_unit`

**IMPORTANT:** Amount is £2,400 — above the £50 HITL threshold. HITL required. Write to Pending_Approval/, do NOT act directly.
""",
}


def ensure_folders():
    print("Creating required folders...")
    for folder in REQUIRED_FOLDERS:
        path = VAULT / folder
        path.mkdir(exist_ok=True)
        print(f"  ✅ {folder}/")


def clear_folders():
    print("\nClearing queue folders (archiving to Archive/)...")
    archive = VAULT / "Archive"
    archive.mkdir(exist_ok=True)

    for folder_name in CLEAR_FOLDERS:
        folder = VAULT / folder_name
        if not folder.exists():
            continue
        files = list(folder.glob("*.md"))
        if not files:
            print(f"  ✅ {folder_name}/ already empty")
            continue
        for f in files:
            dest = archive / f.name
            # Avoid name collision in archive
            if dest.exists():
                stem = f.stem
                suffix = f.suffix
                dest = archive / f"{stem}_archived_{TODAY}{suffix}"
            shutil.move(str(f), str(dest))
            print(f"  📦 {folder_name}/{f.name} → Archive/")
        print(f"  ✅ {folder_name}/ cleared ({len(files)} file(s) archived)")


def write_demo_files():
    print("\nWriting 5 fresh demo files to Needs_Action/...")
    for rel_path, content in DEMO_FILES.items():
        # rel_path uses / as separator, first part is the folder name
        parts = rel_path.split("/", 1)
        folder = parts[0].replace("NEEDS_ACTION", "Needs_Action")
        filename = parts[1]
        dest = VAULT / folder / filename
        dest.write_text(content, encoding="utf-8", newline="\n")
        print(f"  ✅ {folder}/{filename}")


def reset_dashboard():
    print("\nResetting Dashboard.md...")
    dash = VAULT / "Dashboard.md"
    content = dash.read_text(encoding="utf-8")

    # Update the 'updated' timestamp in frontmatter
    import re
    content = re.sub(
        r"updated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
        f"updated: {NOW_ISO}",
        content,
    )

    # Update System Status key rows
    replacements = {
        "Items in Needs_Action": f"| Items in Needs_Action       | 6 ⚠️ Queue has items pending                   |",
        "Items in Inbox": "| Items in Inbox              | 0                                              |",
        "Items Done Today": "| Items Done Today            | 0                                              |",
        "Pending Approvals": "| Pending Approvals           | 0                                              |",
        "Claude Status": "| Claude Status               | ⚪ Awaiting next cycle                          |",
        "Orchestrator": "| Orchestrator                | ⚪ Not running                                  |",
    }

    for key, new_row in replacements.items():
        # Replace the full table row for that key
        content = re.sub(
            r"\| " + re.escape(key) + r"[^\n]*\n",
            new_row + "\n",
            content,
        )

    dash.write_text(content, encoding="utf-8", newline="\n")
    print("  ✅ Dashboard.md updated")


def final_check():
    print("\n" + "=" * 60)
    print("DEMO RESET COMPLETE — Final state check")
    print("=" * 60)

    checks = {
        "Needs_Action/ has 6 files": len(list((VAULT / "Needs_Action").glob("*.md"))) == 6,
        "Inbox/ is empty": len(list((VAULT / "Inbox").glob("*.md"))) == 0,
        "Pending_Approval/ exists & empty": (VAULT / "Pending_Approval").exists() and len(list((VAULT / "Pending_Approval").glob("*.md"))) == 0,
        "Approved/ is empty": len(list((VAULT / "Approved").glob("*.md"))) == 0,
        "Done/ has history files": len(list((VAULT / "Done").glob("*.md"))) > 0,
        "Logs/ has history": len(list((VAULT / "Logs").glob("*.json"))) > 0,
        "Dashboard.md exists": (VAULT / "Dashboard.md").exists(),
        "CLAUDE.md exists": (VAULT / "CLAUDE.md").exists(),
        "Company_Handbook.md exists": (VAULT / "Company_Handbook.md").exists(),
        "orchestrator.py exists": (VAULT / "orchestrator.py").exists(),
    }

    all_ok = True
    for check, result in checks.items():
        icon = "✅" if result else "❌"
        print(f"  {icon} {check}")
        if not result:
            all_ok = False

    print()
    if all_ok:
        print("✅ SYSTEM IS FULLY STAGED AND READY FOR RECORDING")
    else:
        print("❌ SOME CHECKS FAILED — review above before recording")

    print()
    print("NEXT STEPS:")
    print("  1. Start MCP servers (5 terminals):")
    print("       cd mcp_servers/email-mcp && node index.js")
    print("       cd mcp_servers/twitter-mcp && node index.js")
    print("       cd mcp_servers/odoo-mcp && node index.js")
    print("       cd mcp_servers/facebook-instagram-mcp && node index.js")
    print("       cd mcp_servers/linkedin-mcp && node index.js")
    print()
    print("  2. If Briefings/ is empty, generate CEO briefing:")
    print("       uv run python orchestrator.py --briefing")
    print()
    print("  3. Open Obsidian → Dashboard.md (Reading View)")
    print()
    print("  4. When ready to record, trigger the daily cycle:")
    print("       uv run python orchestrator.py --cron")
    print()
    print("  5. After recording, run this script again to reset for next attempt:")
    print("       uv run python reset_demo.py")
    print("=" * 60)


def main():
    print(f"Gold Tier Demo Reset — {TODAY}")
    print(f"Vault: {VAULT}")
    print()
    ensure_folders()
    clear_folders()
    write_demo_files()
    reset_dashboard()
    final_check()


if __name__ == "__main__":
    main()
