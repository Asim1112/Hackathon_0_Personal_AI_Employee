---
type: dashboard
tier: gold
updated: 2026-04-14T08:45:00Z
updated_by: claude_code
version: 3.0
---

# AI Employee Dashboard — Gold Tier

> **Nerve Center** — Real-time summary of business status. Updated automatically by Claude after processing any task.
> Do not edit manually. Claude reads this to understand current state before acting.

---

## System Status

| Field                       | Value                                          |
|-----------------------------|------------------------------------------------|
| Last Updated                | 2026-04-14T08:45:00Z                           |
| **Tier**                    | 🥇 **GOLD**                                    |
| Gmail Watcher               | ⚪ Not yet started (run orchestrator.py)        |
| LinkedIn Watcher            | ⚪ Not yet started                              |
| WhatsApp Watcher            | ⚪ Not yet started                              |
| Twitter Watcher             | ⚪ Not running — demo uses staged queue files      |
| Facebook Watcher            | ⚪ Not running — demo uses staged queue files (MCP live) |
| Odoo Watcher                | ⚪ Not yet started                              |
| Claude Status               | ✅ Cycle 2 complete                             |
| Orchestrator                | ⚪ Not running                                  |
| Items in Needs_Action       | **0 ✅ Queue empty**                            |
| Items in Inbox              | 3                                              |
| Items in Plans              | 0                                              |
| Items In_Progress           | 0                                              |
| Items Done Today            | 6                                              |
| Pending Approvals           | 6                                              |
| Last CEO Briefing           | 2026-04-12 — `CEO_BRIEFING_2026-04-12.md`      |
| Next Weekly Briefing        | Sunday 2026-04-19 23:00                        |

---

## Daily Summary

**2026-04-14 — Tuesday — Cycle 2 Complete ✅**

Daily cycle 2 processing complete. 6 items from `Needs_Action/` processed and moved to `Done/`. All outputs regenerated (previous cycle outputs were cleared). Full audit log written to `Logs/2026-04-14.json`.

**Inbox (3 files — awaiting review):**
- `BRIEFING_2026-04-14.md` — Morning briefing
- `DRAFT_REPLY_2026-04-14_Q2_AI_Integration_Milestone_demo01.md` — Reply to Sarah Johnson (TechCorp Q2 milestone, board deadline Friday)
- `DRAFT_REPLY_2026-04-14_Invoice_Chase_INV-2026-010_Meridian.md` — Payment chase email for £2,400 overdue invoice

**Pending Approval (6 files — awaiting human sign-off):**
- `NEW_CONTACT_REVIEW_Marcus_Webb_LinkedIn_2026-04-14.md` — New contact, Apex Advisory COO, high-value prospect
- `LINKEDIN_DRAFT_AI_Automation_Value_2026-04-14.md` — LinkedIn thought leadership post
- `TWITTER_DRAFT_AI_Employee_Capabilities_2026-04-14.md` — Tweet (228 chars)
- `FACEBOOK_DRAFT_AI_Employee_Announcement_2026-04-14.md` — Facebook Business Page post
- `INSTAGRAM_DRAFT_AI_Employee_Visual_2026-04-14.md` — Instagram post + image
- `ODOO_ACTION_2026-04-14_Invoice_INV-2026-010_Meridian.md` — Odoo invoice create (£2,400)

---

## Accounting Summary (Odoo)

| Metric                | Value          | Period           | Source      |
|-----------------------|----------------|------------------|-------------|
| Monthly Revenue       | — Not synced — | April 2026       | Odoo (stale) |
| Outstanding Invoices  | **£2,400.00** (1 invoice) | 2026-02-24 | Last known |
| Overdue Invoices      | 1 invoice — INV-2026-010 (£2,400, **31 days**) | Due 2026-02-24 | Last known |
| Total Expenses (MTD)  | — Not synced — | —                | Odoo (stale) |

| Invoice | Client | Amount | Days Overdue | Status |
|---------|--------|--------|-------------|--------|
| INV-2026-010 | Meridian Consulting Group | £2,400.00 | **31 days** 🔴 | Odoo action in `Pending_Approval/`. Payment chase draft in `Inbox/`. Both awaiting human approval. |

> **Flag Rule:** Any transaction or payment over £50 must be written to `Pending_Approval/` for human review before action.
> 🔴 **URGENT:** INV-2026-010 is 31 days overdue. Approve `ODOO_ACTION_2026-04-14_Invoice_INV-2026-010_Meridian.md` and the payment chase email to recover £2,400.

---

## Bank Balance

| Account          | Balance   | Last Checked          |
|------------------|-----------|-----------------------|
| Main Operating   | £0.00     | — Not yet synced —    |
| Savings          | £0.00     | — Not yet synced —    |
| Pending Payments | £0.00     | —                     |

---

## Social Media Status

| Platform   | Last Post | Scheduled Posts | Engagement (7d) | Watcher |
|------------|-----------|-----------------|-----------------|---------|
| LinkedIn   | — —       | 1 in `Pending_Approval/` | — — | ⚪ Idle (MCP live — persistent browser) |
| Twitter/X  | — —       | 1 in `Pending_Approval/` | — — | ⚪ Not running (demo mode active) |
| Facebook   | — —       | 1 in `Pending_Approval/` | — — | ⚪ Not running (MCP live — real posts) |
| Instagram  | — —       | 1 in `Pending_Approval/` | — — | 🔧 Uses facebook-instagram-mcp |

> ⚪ Twitter watcher not running — demo uses staged queue files. Twitter MCP posts via demo mode (no 402 error).
> ⚪ Facebook watcher not running — demo uses staged queue files. Facebook & Instagram MCP fully live — real posts confirmed.
> ✅ LinkedIn MCP upgraded to `launchPersistentContext` — persistent browser profile, no more bot detection / #username timeouts.

---

## Pending Messages

| # | Source | From | Subject / Preview | Received | Priority |
|---|--------|------|-------------------|----------|----------|
| — Queue empty ✅ — | — | — | — | — | — |

---

## Active Business Projects

| Project                          | Status       | Next Action                 | Owner | Deadline |
|----------------------------------|--------------|-----------------------------|-------|----------|
| Personal AI Employee — Gold Tier | 🟢 Cycle 2 Done | Review Inbox/ and Pending_Approval/ outputs — approve or reject | Asim  | Today    |
| INV-2026-010 Meridian Collection | 🔴 Urgent    | Approve Odoo action + payment chase email in Inbox/ | Asim  | Immediate |
| TechCorp Q2 Milestone Reply      | 🟡 Drafted   | Review `DRAFT_REPLY_2026-04-14_Q2_AI_Integration_Milestone_demo01.md` → approve by Thursday | Asim | Friday 2026-04-17 |
| Marcus Webb — Discovery Call     | 🟡 Awaiting Approval | Approve `NEW_CONTACT_REVIEW_Marcus_Webb_LinkedIn_2026-04-14.md` → send DM manually | Asim | Today |

---

## Needs Action Queue

| File | Type | Priority | Age |
|------|------|----------|-----|
| — Queue empty ✅ — | — | — | — |

---

## Plans & In Progress

| File | Goal | Status | Steps Done | Steps Total |
|------|------|--------|------------|-------------|
| — No active plans — | — | — | — | — |

---

## Pending Approvals

| File | Action | Contact / Detail | Triggered By | Expires |
|------|--------|-----------------|--------------|---------|
| `NEW_CONTACT_REVIEW_Marcus_Webb_LinkedIn_2026-04-14.md` | New contact approval + suggested DM reply | Marcus Webb, COO — Apex Advisory Partners | SKILL_LinkedIn_Draft | 2026-04-15T08:45:00Z |
| `LINKEDIN_DRAFT_AI_Automation_Value_2026-04-14.md` | Post to LinkedIn | Thought leadership — HITL automation for professional services | SKILL_LinkedIn_Draft | 2026-04-15T08:45:00Z |
| `TWITTER_DRAFT_AI_Employee_Capabilities_2026-04-14.md` | Post tweet (228 chars) | AI Employee Gold Tier capabilities | SKILL_Twitter_Draft | 2026-04-15T08:45:00Z |
| `FACEBOOK_DRAFT_AI_Employee_Announcement_2026-04-14.md` | Post to Facebook Business Page | AI Employee Gold announcement | SKILL_Facebook_Instagram | 2026-04-15T08:45:00Z |
| `INSTAGRAM_DRAFT_AI_Employee_Visual_2026-04-14.md` | Post to Instagram (with image) | AI Employee visual + caption | SKILL_Facebook_Instagram | 2026-04-15T08:45:00Z |
| `ODOO_ACTION_2026-04-14_Invoice_INV-2026-010_Meridian.md` | Create Odoo invoice (£2,400) | Meridian Consulting Group — 31d overdue | SKILL_Odoo_Accounting | 2026-04-15T08:45:00Z |

---

## Inbox (Awaiting Your Review)

| File | Type | For | Priority |
|------|------|-----|----------|
| `BRIEFING_2026-04-14.md` | daily_briefing | Morning summary | NORMAL |
| `DRAFT_REPLY_2026-04-14_Q2_AI_Integration_Milestone_demo01.md` | draft_reply | Sarah Johnson (TechCorp) — Q2 milestone board update | HIGH |
| `DRAFT_REPLY_2026-04-14_Invoice_Chase_INV-2026-010_Meridian.md` | draft_reply | Meridian Consulting Group — INV-2026-010 payment chase £2,400 | URGENT 🔴 |

---

## Recent CEO Briefings

| Date | Period | Revenue vs Target | Key Finding | File |
|------|--------|-------------------|-------------|------|
| 2026-04-12 | Week ending 2026-04-12 | ⚪ At Risk — data pending | INV-2026-010 £2,400 overdue; Twitter/Facebook watchers offline | `Briefings/CEO_BRIEFING_2026-04-12.md` |

---

## Recent Activity Log

| Timestamp | Action | Result |
|-----------|--------|--------|
| 2026-04-14T08:45:00Z | **Daily cycle 2 complete** — 6 items processed. Inbox/: 3 files (briefing, TechCorp reply, Meridian payment chase). Pending_Approval/: 6 files (Marcus Webb new contact + LinkedIn post + Twitter + Facebook + Instagram + Odoo action). All 6 source files → Done/. Log: Logs/2026-04-14.json (21 entries). | ✅ Done |
| 2026-04-14T08:45:00Z | ODOO_2026-04-14_overdue_invoice_INV-2026-010.md — INV-2026-010, Meridian £2,400, 31 days overdue → Odoo create_invoice (Pending_Approval/) + payment chase email (Inbox/) → Done/ | ✅ Escalated |
| 2026-04-14T08:45:00Z | INSTAGRAM_2026-04-14_post_request_demo05.md — Instagram caption + image_url → Pending_Approval/INSTAGRAM_DRAFT_AI_Employee_Visual_2026-04-14.md → Done/ | ✅ Escalated |
| 2026-04-14T08:45:00Z | FACEBOOK_2026-04-14_post_request_demo04.md — Facebook Business Page post (4 paras + engagement question) → Pending_Approval/ → Done/ | ✅ Escalated |
| 2026-04-14T08:45:00Z | TWITTER_2026-04-14_post_request_demo03.md — Tweet (228 chars, 3 hashtags) → Pending_Approval/ → Done/ | ✅ Escalated |
| 2026-04-14T08:45:00Z | LINKEDIN_2026-04-14_enterprise_automation_enquiry_demo02.md — Marcus Webb COO Apex Advisory (new contact, HITL) → NEW_CONTACT_REVIEW + LINKEDIN_DRAFT → Pending_Approval/ → Done/ | ✅ Escalated |
| 2026-04-14T08:45:00Z | EMAIL_2026-04-14_AI_Project_Milestone_demo01.md — Sarah Johnson TechCorp, Q2 milestone + board deadline Friday + Tuesday demo confirmed → DRAFT_REPLY → Inbox/ → Done/ | ✅ Draft written |
| 2026-04-14T08:30:00Z | Cycle 2 briefing generated — 6 items queued. Inbox/BRIEFING_2026-04-14.md written. | ✅ Done |
| 2026-04-14T00:15:00Z | **Demo reset** — `reset_demo.py` run. 6 fresh items staged in `Needs_Action/` (2026-04-14 dates). LinkedIn MCP upgraded to `launchPersistentContext`. All queues cleared. | ✅ Ready |
| 2026-04-13T23:45:07Z | **Daily cycle 7 complete** — 6 items processed. Log: Logs/2026-04-13.json (63 entries) | ✅ Done |
| 2026-04-12T09:30:00Z | **Daily cycle complete (cycle 2)** — 5 items processed. Log: Logs/2026-04-12.json | ✅ Done |
| 2026-04-12T00:00:00Z | **Weekly CEO Briefing generated** — week ending 2026-04-12. Written to `Briefings/CEO_BRIEFING_2026-04-12.md`. | ✅ Done |
| 2026-04-11T20:46:59Z | Twitter watcher error — 402 Payment Required (no API credits) | 🔴 Error |
| 2026-04-11T20:46:59Z | Facebook watcher error — 403 Forbidden on conversations endpoint | 🔴 Error |

---

## Setup Checklist (Gold Tier)

| Item | Status | Action Required |
|------|--------|-----------------|
| Gmail OAuth credentials | ❌ Not configured | Copy `credentials.json` from Google Cloud Console |
| Gmail watcher first-run auth | ❌ Pending | Run `uv run python gmail_watcher.py` once |
| WhatsApp session | ❌ Not authenticated | Run watcher with `--no-headless` to scan QR |
| LinkedIn session | ⚪ Not needed | LinkedIn MCP uses `launchPersistentContext` — no session file required |
| SMTP (email-mcp) | ✅ Configured | Gmail App Password set in `.env` |
| Odoo Community | 🔧 Not installed | See Phase 3 — Docker setup |
| Odoo MCP server | 🔧 Not built | See Phase 3 |
| Twitter API keys | ⚠️ 402 error — demo mode active | `TWITTER_DEMO_MODE=true` in `.env` — bypasses API, moves file to Done/ |
| Meta App credentials | ✅ Working | Facebook Page Access Token refreshed — real posts confirmed |
| Business_Goals.md | ⚠️ Review 33 days overdue | Last reviewed 2026-03-11; update April targets |
| Company_Handbook.md | ⚠️ Review 18 days overdue | Due 2026-03-26 — add Marcus Webb (Apex Advisory, Tier 3) + Meridian (Tier 2) to Section 8 |

---

*Auto-managed by Claude Code — Gold Tier AI Employee v3.0*
