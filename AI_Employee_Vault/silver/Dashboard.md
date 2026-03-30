---
type: dashboard
tier: silver
updated: 2026-03-09T08:00:00Z
updated_by: claude
version: 2.2
---

# AI Employee Dashboard — Silver Tier

> **Nerve Center** — Real-time summary of business status. Updated automatically by Claude after processing any task.
> Do not edit manually. Claude reads this to understand current state before acting.

---

## System Status

| Field                  | Value                                        |
|------------------------|----------------------------------------------|
| Last Updated           | 2026-03-09T08:00:00Z                         |
| **Submission Status**  | ✅ **READY FOR JUDGING**                     |
| Gmail Watcher          | 🟢 Running (token.json active)               |
| LinkedIn Watcher       | 🟢 Running (session authenticated)           |
| WhatsApp Watcher       | 🟢 Running (session authenticated)           |
| Claude Status          | 🟢 Active — morning cycle complete           |
| Scheduler              | 🟢 orchestrator.py running (daemon mode)     |
| Items in Needs_Action  | 0 ✅                                         |
| Items in Inbox         | 2 (briefing + draft email reply)             |
| Items in Plans         | 0                                            |
| Items In_Progress      | 0                                            |
| Items Done Today       | 3                                            |
| Pending Approvals      | 4                                            |

---

## Bank Balance

| Account          | Balance   | Last Checked          |
|------------------|-----------|-----------------------|
| Main Operating   | £0.00     | — Not yet synced —    |
| Savings          | £0.00     | — Not yet synced —    |
| Pending Payments | £0.00     | —                     |

> **Flag Rule:** Any transaction or payment over £50 must be written to `Pending_Approval/` for human review before action. (See Company_Handbook.md Section 6)

---

## Pending Messages

| # | Source    | From                          | Subject / Preview                                         | Received             | Priority |
|---|-----------|-------------------------------|-----------------------------------------------------------|----------------------|----------|
| 1 | Email     | Top Client <topclient@example.com> | Project status update — board meeting next week     | 2026-03-08T21:12Z   | 🔴 URGENT (⚠️ SLA BREACH — Tier 1, ~11h elapsed) |
| 2 | WhatsApp  | John Smith                    | Invoice confirmation — "need to process ASAP"             | 2026-03-08T21:12Z   | 🟡 HIGH (new contact) |
| 3 | LinkedIn  | Jane Doe                      | Consulting services enquiry — wants call this week        | 2026-03-08T21:12Z   | 🟡 HIGH (new contact, business_opportunity) |

> All 3 messages triaged. Draft replies and approval requests ready in Pending_Approval/.

---

## Active Business Projects

| Project                         | Status         | Next Action                                    | Owner | Deadline |
|---------------------------------|----------------|------------------------------------------------|-------|----------|
| Personal AI Employee Hackathon  | 🟢 Complete    | Silver tier built, tested, running              | Asim  | —        |
| Jane Doe — Consulting Discovery | 🟡 Pending     | Approve LinkedIn DM reply + LinkedIn post      | Asim  | Today    |
| Top Client — Project Status     | 🔴 URGENT      | Approve email reply (SLA breached)             | Asim  | ASAP     |

---

## Needs Action Queue

| File | Type | Priority | Age |
|------|------|----------|-----|
| — Queue is empty ✅ — | — | — | — |

---

## Plans & In Progress

| File | Goal | Status | Steps Done | Steps Total |
|------|------|--------|------------|-------------|
| — No active plans — | — | — | — | — |

---

## Pending Approvals

| File | Action | Contact | Triggered By | Expires |
|------|--------|---------|--------------|---------|
| EMAIL_REVIEW_Project_Status_2026-03-09.md | Send email reply (via email-mcp) | Top Client | SKILL_Gmail_Triage | 2026-03-10T08:00Z |
| NEW_CONTACT_REVIEW_John_Smith_WhatsApp_2026-03-09.md | Send WhatsApp reply (manual) | John Smith | SKILL_WhatsApp_Triage | 2026-03-10T08:00Z |
| NEW_CONTACT_REVIEW_Jane_Doe_LinkedIn_DM_2026-03-09.md | Send LinkedIn DM reply (manual) | Jane Doe | SKILL_LinkedIn_Draft | 2026-03-10T08:00Z |
| LINKEDIN_DRAFT_Consulting_Services_2026-03-09.md | Post to LinkedIn (via linkedin-mcp) | — | SKILL_LinkedIn_Draft | 2026-03-10T08:00Z |

> Move files from `Pending_Approval/` to `Approved/` or `Rejected/` to action them.
> **WhatsApp and LinkedIn DM replies must be sent manually — no MCP available for those channels.**
> **Email reply will be sent automatically by email-mcp when moved to /Approved/.**

---

## LinkedIn Queue

| Draft File | Topic | Post Type | Created | Status |
|------------|-------|-----------|---------|--------|
| LINKEDIN_DRAFT_Consulting_Services_2026-03-09.md | Value of Expert Consulting — Getting Projects Right | Thought Leadership | 2026-03-09 | ⏳ Awaiting approval |

> Move to `Approved/` to trigger `linkedin-mcp` to post automatically.

---

## Recent Activity Log

| Timestamp | Action | Result |
|-----------|--------|--------|
| 2026-03-09T08:00:00Z | SKILL_Update_Dashboard — dashboard refreshed after full morning cycle | ✅ Done |
| 2026-03-09T08:00:00Z | SKILL_Process_Needs_Action — 3 items processed, moved to Done/ | ✅ Done |
| 2026-03-09T08:00:00Z | SKILL_Reasoning_Loop — 0 complex tasks detected | ✅ Done |
| 2026-03-09T08:00:00Z | SKILL_LinkedIn_Draft — Jane Doe (business_opportunity): DM draft + LinkedIn post created | ✅ Done → Pending_Approval/ |
| 2026-03-09T08:00:00Z | SKILL_WhatsApp_Triage — John Smith (invoice): new contact review + draft reply created | ✅ Done → Pending_Approval/ |
| 2026-03-09T08:00:00Z | SKILL_Gmail_Triage — Top Client (project status): ⚠️ SLA BREACH — draft reply + email review created | ✅ Done → Pending_Approval/ |
| 2026-03-09T08:00:00Z | SKILL_Daily_Briefing — briefing generated (ACTION_NEEDED — 3 items, 1 SLA breach) | ✅ Done → Inbox/ |
| 2026-03-09T08:00:00Z | SKILL_Update_Dashboard — dashboard refreshed for Monday morning cycle | ✅ Done |
| 2026-03-09T08:00:00Z | SKILL_Process_Needs_Action — queue empty, nothing to process | ✅ Done |
| 2026-03-09T08:00:00Z | SKILL_Reasoning_Loop — 0 complex tasks detected | ✅ Done |
| 2026-03-09T08:00:00Z | SKILL_LinkedIn_Draft — 0 LinkedIn opportunities in queue | ✅ Done |
| 2026-03-09T08:00:00Z | SKILL_WhatsApp_Triage — 0 WhatsApp items in queue | ✅ Done |
| 2026-03-09T08:00:00Z | SKILL_Gmail_Triage — 0 email items in queue | ✅ Done |
| 2026-03-09T08:00:00Z | SKILL_Daily_Briefing — briefing generated (ALL_CLEAR, Monday full-automation day) | ✅ Done |
| 2026-03-08T08:00:00Z | SKILL_Daily_Briefing — morning briefing generated (ALL_CLEAR, Sunday monitoring-only day) | ✅ Done |
| 2026-03-08T08:00:00Z | SKILL_Gmail_Triage — 0 email items in queue | ✅ Done |
| 2026-03-08T08:00:00Z | SKILL_WhatsApp_Triage — 0 WhatsApp items in queue | ✅ Done |
| 2026-03-08T08:00:00Z | SKILL_LinkedIn_Draft — 0 LinkedIn opportunities in queue | ✅ Done |
| 2026-03-08T08:00:00Z | SKILL_Reasoning_Loop — 0 complex tasks detected | ✅ Done |
| 2026-03-08T08:00:00Z | SKILL_Process_Needs_Action — queue empty, nothing to process | ✅ Done |
| 2026-03-08T08:00:00Z | SKILL_Update_Dashboard — dashboard refreshed | ✅ Done |

---

## Daily Summary

**2026-03-09 — Monday Morning Briefing (Second Cycle)**

Three items arrived overnight on Sunday (monitoring-only day) and were held until this morning. All 3 have now been fully processed:

1. **Top Client email** (⚠️ SLA BREACH — Tier 1, ~11h): Draft reply created; email-mcp approval request waiting in `Pending_Approval/`. Prioritise this immediately.
2. **John Smith WhatsApp** (invoice, new contact, Tier 4): New contact review + draft reply in `Pending_Approval/`. Manual send required after approval.
3. **Jane Doe LinkedIn DM** (business_opportunity, new contact, Tier 3): DM draft + thought-leadership post both in `Pending_Approval/`. Manual DM send; linkedin-mcp will handle post.

**Queue:** 0 items remaining. **Priority:** ACTION_NEEDED 🟡 — 4 pending approvals require your decision today.
**Pending decisions:** 4 approvals (all expire 2026-03-10T08:00Z).
**Plans active:** 0.

---

## ⚠️ Setup Gaps (Action Required)

| Item | Status | Fix |
|------|--------|-----|
| Gmail Watcher | 🟡 Needs first-run auth | Run `uv run python gmail_watcher.py` once (30 seconds) |
| Company_Handbook.md Section 8 | ❌ Placeholder values | Fill in your real Key Contacts |
| WhatsApp Watcher | 🟢 Configured | Session authenticated |
| LinkedIn Watcher | 🟢 Configured | Session authenticated |

---

*Auto-managed by Claude Code — Silver Tier AI Employee v2.2*
