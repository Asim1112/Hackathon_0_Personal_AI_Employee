---
type: dashboard
tier: gold
updated: 2026-03-14T10:30:04Z
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
| Last Updated                | 2026-03-14T10:30:04Z                           |
| **Tier**                    | 🥇 **GOLD**                                    |
| Gmail Watcher               | ⚪ Not yet started (run orchestrator.py)        |
| LinkedIn Watcher            | ⚪ Not yet started                              |
| WhatsApp Watcher            | ⚪ Not yet started                              |
| Twitter Watcher             | 🔧 Pending implementation                       |
| Facebook Watcher            | 🔧 Pending implementation                       |
| Odoo Watcher                | 🔧 Pending implementation                       |
| Claude Status               | ✅ Processing cycle complete                    |
| Orchestrator                | ⚪ Not running                                  |
| Items in Needs_Action       | 0 ✅ Queue clear                               |
| Items in Inbox              | 1                                              |
| Items in Plans              | 0                                              |
| Items In_Progress           | 0                                              |
| Items Done Today            | 3                                              |
| Pending Approvals           | 3                                              |
| Last CEO Briefing           | — None yet —                                   |
| Next Weekly Briefing        | Sunday 23:00                                   |

---

## Accounting Summary (Odoo)

| Metric                | Value          | Period           | Source      |
|-----------------------|----------------|------------------|-------------|
| Monthly Revenue       | — Not synced — | —                | Odoo        |
| Outstanding Invoices  | £1,500.00 (net) / £1,800.00 incl. VAT | 2026-03-14 | ODOO_REVIEW_Invoice_Demo_Client_Ltd_2026-03-14.md (⏳ pending approval) |
| Overdue Invoices      | — Not synced — | —                | Odoo        |
| Total Expenses (MTD)  | — Not synced — | —                | Odoo        |

> **Flag Rule:** Any transaction or payment over £50 must be written to `Pending_Approval/` for human review before action.
> ⚠️ Invoice for Demo Client Ltd (£1,500 net / £1,800 incl. VAT, AI Consulting 10hrs, ref PROJECT-001) — awaiting approval in `Pending_Approval/ODOO_REVIEW_Invoice_Demo_Client_Ltd_2026-03-14.md`
> Rate used: £150/hr from Business_Goals.md Service Rate Card.

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
| LinkedIn   | — —       | 0               | — —             | ⚪ Idle  |
| Twitter/X  | — —       | 1 pending approval (`TWITTER_DRAFT_AI_Agents_Reply_techfounder_2026-03-14.md`, 190 chars reply to @techfounder tweet_id: 1234567890) | — — | 🔧 TBD  |
| Facebook   | — —       | 0               | — —             | 🔧 TBD  |
| Instagram  | — —       | 0               | — —             | 🔧 TBD  |

---

## Pending Messages

| # | Source | From | Subject / Preview | Received | Priority |
|---|--------|------|-------------------|----------|----------|
| — | — | — Queue clear ✅ (3 processed 2026-03-14T10:30:04Z) — | — | — |

---

## Active Business Projects

| Project                          | Status       | Next Action                 | Owner | Deadline |
|----------------------------------|--------------|-----------------------------|-------|----------|
| Personal AI Employee — Gold Tier | 🟡 Building  | Complete Gold tier scaffold | Asim  | —        |

---

## Needs Action Queue

| File | Type | Priority | Age |
|------|------|----------|-----|
| — Queue is empty ✅ — | — | — | — (3 processed 2026-03-14T10:30:04Z) |

---

## Plans & In Progress

| File | Goal | Status | Steps Done | Steps Total |
|------|------|--------|------------|-------------|
| — No active plans — | — | — | — | — |

---

## Pending Approvals

| File | Action | Contact | Triggered By | Expires |
|------|--------|---------|--------------|---------|
| NEW_CONTACT_REVIEW_John_Smith_Email_2026-03-14.md | Send email reply — Project Status Update | John Smith (john.client@example.com) | SKILL_Gmail_Triage | 2026-03-15T10:30:00Z |
| ODOO_REVIEW_Invoice_Demo_Client_Ltd_2026-03-14.md | Create Odoo invoice — £1,500 net / £1,800 incl. VAT, ref PROJECT-001 | Demo Client Ltd | SKILL_Odoo_Accounting | 2026-03-15T10:30:00Z |
| TWITTER_DRAFT_AI_Agents_Reply_techfounder_2026-03-14.md | Post reply tweet — @techfounder mention (190 chars, reply_to_tweet_id: 1234567890) | @techfounder (Tech Founder) | SKILL_Twitter_Draft | 2026-03-15T10:30:00Z |

> ⚠️ **Action required:** 3 items awaiting your approval. Review and move each file to `/Approved/` or `/Rejected/` by 2026-03-15T10:30:00Z.
> 1. **Email:** Draft reply is in `Inbox/DRAFT_REPLY_Project_Status_Update_2026-03-14.md` — **fill in actual project status before approving.** Also add John Smith to Key Contacts in Company_Handbook.md Section 8.
> 2. **Odoo:** Invoice for Demo Client Ltd (PROJECT-001) — verify VAT status and add partner email before approving.
> 3. **Twitter:** Reply to @techfounder (190 chars) — review tone and content before approving.

---

## Recent CEO Briefings

| Date | Period | Revenue vs Target | Key Finding | File |
|------|--------|-------------------|-------------|------|
| — No briefings yet — | — | — | — | — |

---

## Recent Activity Log

| Timestamp | Action | Result |
|-----------|--------|--------|
| 2026-03-14T10:30:04Z | Processing cycle complete — 3 items processed, 5 files written (1 Inbox/, 3 Pending_Approval/, 3 Done/), Needs_Action/ clear, Logs/2026-03-14.json created | ✅ Done |
| 2026-03-14T10:30:03Z | TWITTER_2026-03-14_mention_demo.md — @techfounder positive AI agents mention, classified as engagement opportunity → reply tweet drafted (190 chars, reply_to_tweet_id: 1234567890) → TWITTER_DRAFT_AI_Agents_Reply_techfounder_2026-03-14.md to Pending_Approval/ → Done/ | ✅ Escalated |
| 2026-03-14T10:30:02Z | ODOO_2026-03-14_Invoice_Request.md — Demo Client Ltd, AI Consulting 10hrs × £150 = £1,500 net (£1,800 incl. 20% VAT), ref PROJECT-001 → ODOO_REVIEW_Invoice_Demo_Client_Ltd_2026-03-14.md to Pending_Approval/ → Done/ | ✅ Escalated |
| 2026-03-14T10:30:01Z | EMAIL_2026-03-14_Client_Status_Update.md — John Smith project status enquiry (Tier 4, new contact, ⚠️ SLA borderline 72h) → DRAFT_REPLY to Inbox/DRAFT_REPLY_Project_Status_Update_2026-03-14.md + NEW_CONTACT_REVIEW to Pending_Approval/ → Done/ | ✅ Escalated |
| 2026-03-14T10:00:04Z | Previous processing cycle — queue clear | ✅ Done |
| 2026-03-11T09:15:00Z | Gold tier vault scaffolded — ready for implementation | ✅ Done |

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
| Business_Goals.md | ⚠️ Template only | Fill in real revenue targets |
| Company_Handbook.md | ⚠️ Silver copy | Update Key Contacts — add John Smith if known client |

---

*Auto-managed by Claude Code — Gold Tier AI Employee v3.0*
