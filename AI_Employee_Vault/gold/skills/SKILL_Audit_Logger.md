# SKILL_Audit_Logger — Agent Skill

## Purpose
Write structured JSON audit log entries for every action the AI Employee takes.
This is a Gold-tier requirement — every action must be traceable.

Logs are stored in `Logs/YYYY-MM-DD.json` (one file per day).

---

## When to Invoke

After EVERY completed action, including:
- Triaging an email, WhatsApp, Twitter, or Facebook item
- Drafting a reply, social post, or Odoo invoice
- Creating a plan in `Plans/`
- Moving a file to any folder
- Writing an approval request to `Pending_Approval/`
- Generating a briefing
- Completing a `TASK_COMPLETE` cycle

This skill is called at the END of each processing cycle (after all other skills).
If multiple actions were taken in one session, write one log entry per action.

---

## Log Entry Schema

```json
{
  "timestamp": "<ISO 8601 — e.g. 2026-03-11T09:15:32Z>",
  "action_type": "<see Action Types below>",
  "actor": "claude_code",
  "target": "<filename, contact name, or platform>",
  "skill_used": "<SKILL_NAME or null>",
  "approval_status": "<not_required | pending | approved | rejected>",
  "result": "<success | escalated | error>",
  "notes": "<one sentence describing what happened>"
}
```

---

## Action Types Reference

| action_type | When to use |
|---|---|
| `email_triage` | Processed an email from Needs_Action/ |
| `email_draft_created` | Wrote a draft reply to Inbox/ |
| `email_sent` | Email confirmed via email-mcp (Done/ file) |
| `whatsapp_triage` | Processed a WhatsApp message |
| `whatsapp_draft_created` | Wrote a WhatsApp draft reply |
| `linkedin_triage` | Processed a LinkedIn item |
| `linkedin_draft_created` | Wrote a LinkedIn post draft |
| `twitter_triage` | Processed a Twitter mention/DM |
| `twitter_draft_created` | Wrote a tweet draft |
| `facebook_triage` | Processed a Facebook/Instagram item |
| `facebook_draft_created` | Wrote a Facebook/Instagram post draft |
| `social_posted` | Post confirmed via MCP (Done/ file) |
| `odoo_draft_created` | Wrote an Odoo action to Pending_Approval/ |
| `odoo_invoice_created` | Invoice created in Odoo (odoo-mcp confirmed) |
| `odoo_invoice_confirmed` | Invoice posted in Odoo |
| `odoo_overdue_alert` | Processed an overdue invoice alert |
| `odoo_sync_complete` | Accounting/Current_Month.md refreshed |
| `plan_created` | Created a PLAN_ file in Plans/ |
| `plan_progressed` | Ticked checkboxes in a plan in In_Progress/ |
| `plan_completed` | Plan moved to Done/ |
| `approval_requested` | Wrote to Pending_Approval/ |
| `approval_granted` | Human moved file to Approved/ (logged retroactively) |
| `approval_rejected` | Human moved file to Rejected/ |
| `daily_briefing_generated` | SKILL_Daily_Briefing completed |
| `ceo_briefing_generated` | SKILL_Weekly_CEO_Briefing completed |
| `dashboard_updated` | Dashboard.md refreshed |
| `new_contact_flagged` | Unknown sender/contact flagged for review |
| `escalated_to_human` | Item escalated — legal/complaint/high value |
| `error_logged` | An error occurred during processing |

---

## How to Write the Log

### Step 1 — Determine today's log file path

```
Logs/<YYYY-MM-DD>.json   where YYYY-MM-DD = today's date
```

Example: `Logs/2026-03-11.json`

### Step 2 — Check if the file exists

- **If it doesn't exist:** Create it as an empty JSON array `[]`
- **If it exists:** Read the current array

### Step 3 — Append your entry/entries

For each action taken in this session, append one JSON object to the array.

**Important:** Write the complete updated array back to the file (not just the new entry).

### Step 4 — Mark source files as logged

For any Needs_Action/ or Done/ files processed in this session, update their
frontmatter: `logged: true`

---

## Example: Single Action Session

Session processed one email → wrote draft reply:

```json
[
  {
    "timestamp": "2026-03-11T09:15:32Z",
    "action_type": "email_triage",
    "actor": "claude_code",
    "target": "EMAIL_2026-03-11_Invoice_Query_abc123.md",
    "skill_used": "SKILL_Gmail_Triage",
    "approval_status": "not_required",
    "result": "success",
    "notes": "Triaged invoice query from client@example.com — draft reply created in Inbox/"
  },
  {
    "timestamp": "2026-03-11T09:15:45Z",
    "action_type": "email_draft_created",
    "actor": "claude_code",
    "target": "DRAFT_REPLY_Invoice_Query_2026-03-11.md",
    "skill_used": "SKILL_Gmail_Triage",
    "approval_status": "pending",
    "result": "success",
    "notes": "Draft reply to invoice query written to Inbox/ — awaiting review before send"
  }
]
```

---

## Example: Error Case

```json
{
  "timestamp": "2026-03-11T09:20:00Z",
  "action_type": "error_logged",
  "actor": "claude_code",
  "target": "EMAIL_2026-03-11_Malformed_xyz.md",
  "skill_used": "SKILL_Gmail_Triage",
  "approval_status": "not_required",
  "result": "error",
  "notes": "File had no frontmatter — could not classify. Left in Needs_Action/ for manual review."
}
```

---

## Daily Log Retention

- Logs are kept indefinitely (small JSON files — negligible storage)
- `audit_logger.py` (Python utility) can be used to export or query logs
- Never delete log files — they are the permanent audit trail

---

## After Writing the Log

Update `Dashboard.md` → **System Status** table: set `Last Log Entry` to the current timestamp.
