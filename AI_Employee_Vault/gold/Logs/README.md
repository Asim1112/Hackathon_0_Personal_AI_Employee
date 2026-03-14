# Logs/

This folder contains **structured JSON audit logs** for every action the AI Employee takes.

## File Naming
`YYYY-MM-DD.json` — One file per day

## Log Entry Format
```json
{
  "timestamp": "2026-03-11T08:00:00Z",
  "action_type": "email_triage",
  "actor": "claude_code",
  "target": "EMAIL_2026-03-11_Invoice_Query_abc123.md",
  "skill_used": "SKILL_Gmail_Triage",
  "approval_status": "not_required",
  "result": "success",
  "notes": "Triaged as DRAFT_REPLY — known contact, sent to Inbox/"
}
```

## Action Types
| Type | Description |
|------|-------------|
| `email_triage` | Email processed via SKILL_Gmail_Triage |
| `whatsapp_triage` | WhatsApp message processed |
| `linkedin_draft` | LinkedIn post draft created |
| `twitter_draft` | Tweet draft created |
| `facebook_draft` | Facebook/Instagram post draft created |
| `odoo_query` | Odoo financial data queried |
| `odoo_draft` | Odoo invoice/record drafted (pending approval) |
| `plan_created` | Multi-step plan created in Plans/ |
| `plan_completed` | Plan moved to Done/ |
| `approval_requested` | File written to Pending_Approval/ |
| `ceo_briefing` | Weekly CEO briefing generated |
| `dashboard_update` | Dashboard.md refreshed |

## Retention
Logs are retained for **90 days**. Files older than 90 days are moved to `Archive/Logs/`.

## Note
This folder is written by Claude Code (via SKILL_Audit_Logger) after every action.
It provides a complete, reviewable audit trail of all AI Employee decisions.
