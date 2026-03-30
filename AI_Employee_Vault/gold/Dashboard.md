---
type: dashboard
tier: gold
updated: 2026-03-26T09:52:00Z
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
| Last Updated                | 2026-03-26T09:52:00Z                           |
| **Tier**                    | 🥇 **GOLD**                                    |
| Gmail Watcher               | ⚪ Not yet started (run orchestrator.py)        |
| LinkedIn Watcher            | ⚪ Not yet started                              |
| WhatsApp Watcher            | ⚪ Not yet started                              |
| Twitter Watcher             | 🔧 Pending implementation                       |
| Facebook Watcher            | 🔧 Pending implementation                       |
| Odoo Watcher                | 🔧 Pending implementation                       |
| Claude Status               | ✅ Processing cycle complete (2026-03-26T09:52:00Z) |
| Orchestrator                | ⚪ Not running                                  |
| Items in Needs_Action       | 0 ✅ Queue clear                               |
| Items in Inbox              | 3 (BRIEFING_2026-03-26 + DRAFT_REPLY_Q2_AI_Project_Milestone + DRAFT_REPLY_Overdue_Invoice_Meridian_Consulting) |
| Items in Plans              | 0                                              |
| Items In_Progress           | 0                                              |
| Items Done Today            | 5 (Cycle 2 — 2026-03-26T09:52:00Z)             |
| Pending Approvals           | 5 (all from today's Cycle 2)                   |
| Last CEO Briefing           | — None yet —                                   |
| Next Weekly Briefing        | Sunday 23:00                                   |

---

## Daily Summary

**2026-03-26 — Cycle 2 Complete (09:52 UTC)**

Full daily workflow complete. 5 items processed across 5 channels (Email, LinkedIn, Twitter, Facebook, Odoo). 8 files written: 3 to Inbox/ (morning briefing + Q2 milestone email draft + Meridian INV-2026-010 payment chase), 5 to Pending_Approval/ (new contact review Marcus Webb + LinkedIn draft + Twitter draft + Facebook draft + Odoo invoice INV-2026-010). All 5 source files → Done/. Needs_Action/ is empty.

**Queue:** 0 items remaining ✅ **Priority:** ACTION_NEEDED — 5 approvals awaiting human decision.

**URGENT — Overdue invoice:**
- INV-2026-010: Meridian Consulting Group, £2,400.00, **31 days overdue** (due 2026-02-24)
- Odoo create_invoice action in Pending_Approval/ — approve to create in Odoo, then approve payment chase in Inbox/

**High-value lead:** Marcus Webb, COO Apex Advisory Partners (45 people, finserv advisory) — new contact, 3 pain point matches. Discovery call window is "next week" — reply by EOD tomorrow to secure slot.

**Existing client deadline:** Sarah Johnson (TechCorp Ltd) needs Q2 AI Integration milestone update for Friday board meeting. Draft in Inbox/ — fill 2x [PLACEHOLDER] items before approving send.

---

## Accounting Summary (Odoo)

| Metric                | Value          | Period           | Source      |
|-----------------------|----------------|------------------|-------------|
| Monthly Revenue       | — Not synced — | —                | Odoo        |
| Outstanding Invoices  | **£2,400.00** (1 active invoice) | 2026-03-26 | Odoo watcher (Cycle 2) |
| Overdue Invoices      | 1 invoice — INV-2026-010 (£2,400, 31 days) | 2026-03-26 | Odoo watcher |
| Total Expenses (MTD)  | — Not synced — | —                | Odoo        |

| Invoice | Client | Amount | Days Overdue | Status |
|---------|--------|--------|-------------|--------|
| INV-2026-010 | Meridian Consulting Group | £2,400.00 | 31 days | 🔴 Odoo create_invoice action in Pending_Approval/ + payment chase in Inbox/ (Cycle 2 — 2026-03-26) |

> **Flag Rule:** Any transaction or payment over £50 must be written to `Pending_Approval/` for human review before action.
> ⚠️ **Action needed:** INV-2026-010 is 31 days overdue. Approve Odoo action + payment chase email to recover £2,400.

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
| LinkedIn   | — —       | 1 pending approval (`LINKEDIN_DRAFT_Enterprise_Automation_Consulting_2026-03-26.md`) | — — | ⚪ Idle  |
| Twitter/X  | — —       | 1 pending approval (`TWITTER_DRAFT_AI_Employee_Capabilities_2026-03-26.md`) | — — | 🔧 TBD  |
| Facebook   | — —       | 1 pending approval (`FACEBOOK_DRAFT_AI_Employee_Professional_Services_2026-03-26.md`) | — — | 🔧 TBD  |
| Instagram  | — —       | 0               | — —             | 🔧 TBD  |

> ⚠️ LinkedIn posting quota: max 3/week, 1/day. 1 draft queued — approve when ready. Do NOT approve more than 1 LinkedIn post per day.

---

## Pending Messages

| # | Source | From | Subject / Preview | Received | Priority |
|---|--------|------|-------------------|----------|----------|
| — | — | — Queue clear ✅ (5 processed 2026-03-26, 10 processed 2026-03-25) — | — | — |

---

## Active Business Projects

| Project                          | Status       | Next Action                 | Owner | Deadline |
|----------------------------------|--------------|-----------------------------|-------|----------|
| Personal AI Employee — Gold Tier | 🟡 Building  | Complete Gold tier scaffold | Asim  | —        |

---

## Needs Action Queue

| File | Type | Priority | Age |
|------|------|----------|-----|
| — Queue is empty ✅ — | — | — | — (5 processed 2026-03-26 Cycle 2) |

---

## Plans & In Progress

| File | Goal | Status | Steps Done | Steps Total |
|------|------|--------|------------|-------------|
| — No active plans — | — | — | — | — |

---

## Pending Approvals

| File | Action | Contact | Triggered By | Expires |
|------|--------|---------|--------------|---------|
| **— 2026-03-26 (Cycle 2) —** | | | | |
| NEW_CONTACT_REVIEW_Marcus_Webb_LinkedIn_2026-03-26.md | LinkedIn DM reply — Enterprise AI automation enquiry (COO, 45-person firm, discovery call "next week") | Marcus Webb, COO — Apex Advisory Partners | SKILL_LinkedIn_Draft | 2026-03-27T09:35:00Z |
| LINKEDIN_DRAFT_Enterprise_Automation_Consulting_2026-03-26.md | Post LinkedIn thought leadership — enterprise automation for professional services (~175 words, 5 hashtags) | — | SKILL_LinkedIn_Draft | 2026-03-27T09:38:00Z |
| TWITTER_DRAFT_AI_Employee_Capabilities_2026-03-26.md | Post standalone tweet — 5-channel monitoring + HITL (265 chars, post_tweet) | — | SKILL_Twitter_Draft | 2026-03-27T09:42:00Z |
| FACEBOOK_DRAFT_AI_Employee_Professional_Services_2026-03-26.md | Post Facebook Business Page — AI Employee for professional services (4 paragraphs + engagement question) | — | SKILL_Facebook_Instagram | 2026-03-27T09:45:00Z |
| ODOO_REVIEW_Invoice_Meridian_Consulting_2026-03-26.md | Create Odoo invoice — INV-2026-010, £2,400.00, Meridian Consulting Group (AI Strategy Feb 2026, 31 days overdue) | Meridian Consulting Group | SKILL_Odoo_Accounting | 2026-03-27T09:48:00Z |

> ⚠️ **Action required:** 5 items awaiting your approval. Priority order:
>
> 1. 🔴 **CRITICAL — Overdue invoice (£2,400, 31 days):**
>    - Approve `ODOO_REVIEW_Invoice_Meridian_Consulting_2026-03-26.md` → creates Odoo draft invoice
>    - Then add recipient email to `Inbox/DRAFT_REPLY_Overdue_Invoice_Meridian_Consulting_2026-03-26.md` and approve
> 2. 🟡 **High-value lead — next-week call window:** `NEW_CONTACT_REVIEW_Marcus_Webb_LinkedIn_2026-03-26.md` — reply by EOD tomorrow
> 3. 🟡 **Email reply — board deadline Friday:** `Inbox/DRAFT_REPLY_Q2_AI_Project_Milestone_2026-03-26.md` — fill 2x [PLACEHOLDER] first
> 4. 🟢 **LinkedIn post:** `LINKEDIN_DRAFT_Enterprise_Automation_Consulting_2026-03-26.md` — max 1/day quota
> 5. 🟢 **Twitter + Facebook:** Queue across this week

---

## Recent CEO Briefings

| Date | Period | Revenue vs Target | Key Finding | File |
|------|--------|-------------------|-------------|------|
| — No briefings yet — | — | — | — | — |

---

## Recent Activity Log

| Timestamp | Action | Result |
|-----------|--------|--------|
| 2026-03-26T09:52:00Z | **2026-03-26 Cycle 2 complete** — 5 items processed (email, linkedin new contact + post, twitter, facebook, odoo). 8 files written: 3 Inbox/ (briefing + Q2 milestone draft + Meridian INV-2026-010 payment chase), 5 Pending_Approval/ (new contact review + linkedin draft + twitter draft + facebook draft + odoo invoice). All 5 source files → Done/. Needs_Action/ empty. Log: Logs/2026-03-26.json | ✅ Done |
| 2026-03-26T08:55:00Z | **2026-03-26 Cycle 1 complete** — 5 items processed (email, linkedin new contact, twitter, facebook, odoo). 7 files written: 2 Inbox/ (Q2 milestone draft + Meridian INV-2026-010 payment chase), 5 Pending_Approval/ (new contact review + linkedin draft + twitter draft + facebook draft + odoo invoice). All 5 source files → Done/. Needs_Action/ clear. Log: Logs/2026-03-26.json | ✅ Done |
| 2026-03-25T10:40:00Z | Cycle 2 complete — 5 items processed (email, linkedin x2, twitter, facebook, odoo). 7 files written: 2 Inbox/ (Q2 milestone draft + Meridian payment chase), 5 Pending_Approval/. 5 source files → Done/. Needs_Action/ clear. | ✅ Done |
| 2026-03-25T10:32:00Z | ODOO_2026-03-25_overdue_invoice_INV-2026-009.md — INV-2026-009, Meridian Consulting Group, £2,400 24 days overdue → create_invoice action to Pending_Approval/ + payment chase to Inbox/ → Done/ | ✅ Escalated |
| 2026-03-25T10:25:00Z | FACEBOOK_2026-03-25_post_request_demo04.md — admin task, AI Employee for professional services announcement → FACEBOOK_DRAFT to Pending_Approval/ → Done/ | ✅ Escalated |
| 2026-03-25T10:20:00Z | TWITTER_2026-03-25_post_request_demo03.md — admin task, standalone post_tweet AI Employee capabilities (247 chars) → TWITTER_DRAFT to Pending_Approval/ → Done/ | ✅ Escalated |
| 2026-03-25T10:15:00Z | LINKEDIN_2026-03-25_enterprise_automation_enquiry_demo02.md — Marcus Webb COO Apex Advisory Partners, new contact, enterprise automation enquiry → NEW_CONTACT_REVIEW + LINKEDIN_DRAFT to Pending_Approval/ → Done/ | ✅ Escalated |
| 2026-03-25T10:05:00Z | EMAIL_2026-03-25_AI_Project_Milestone_demo01.md — Sarah Johnson TechCorp Ltd (existing contact), Q2 AI Integration milestone update for Friday board meeting → DRAFT_REPLY to Inbox/ → Done/ | ✅ Draft written |
| 2026-03-25T09:00:00Z | Full daily workflow complete — 5 items processed (email, linkedin, twitter, facebook, odoo). 8 files written: 3 Inbox/ (briefing + 2 drafts), 5 Pending_Approval/. 5 source files → Done/. Needs_Action/ clear. | ✅ Done |
| 2026-03-24T10:16:00Z | Full daily workflow complete — 5 items processed (email, linkedin, twitter, facebook, odoo). 7 files written: 2 Inbox/, 5 Pending_Approval/. 5 source files → Done/. Needs_Action/ clear. | ✅ Done |

---

## Setup Checklist (Gold Tier)

| Item | Status | Action Required |
|------|--------|-----------------|
| Gmail OAuth credentials | ❌ Not configured | Copy `credentials.json` from Google Cloud Console |
| Gmail watcher first-run auth | ❌ Pending | Run `uv run python gmail_watcher.py` once |
| WhatsApp session | ❌ Not authenticated | Run watcher with `--no-headless` to scan QR |
| LinkedIn session | ❌ Not authenticated | Run watcher with `HEADLESS=false` |
| SMTP (email-mcp) | ❌ Not configured | Edit `.env` with Gmail App Password |
| Odoo Community | 🔧 Not installed | See Phase 3 — Docker setup |
| Odoo MCP server | 🔧 Not built | See Phase 3 |
| Twitter API keys | 🔧 Not configured | See Phase 4 |
| Meta App credentials | 🔧 Not configured | See Phase 5 |
| Business_Goals.md | ⚠️ Review overdue | Next review was due 2026-03-18 — update revenue targets |
| Company_Handbook.md | ⚠️ Review due 2026-03-26 | Add James Carter (Nexus Ventures, Tier 3), Marcus Webb (Apex Advisory Partners, Tier 3), Bright Solutions Ltd, Meridian Consulting Group to Key Contacts (Section 8) |

---

*Auto-managed by Claude Code — Gold Tier AI Employee v3.0*
