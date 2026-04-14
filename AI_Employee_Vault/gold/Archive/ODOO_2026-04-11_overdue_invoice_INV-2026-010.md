---
type: odoo_alert
status: processed
platform: odoo
action_hint: create_invoice
partner: "Meridian Consulting Group"
invoice_ref: "INV-2026-010"
amount_due: 2400.00
currency: GBP
overdue_days: 47
received: 2026-04-11T08:25:00Z
priority: high
logged: false
contact_email: asimhussain8000@gmail.com
processed_at: 2026-04-12T08:25:00Z
processed_by: claude_code
skill_used: SKILL_Odoo_Accounting
outcome: "Odoo invoice action → Pending_Approval/ODOO_ACTION_2026-04-12_Invoice_Meridian.md | Payment chase → Inbox/DRAFT_REPLY_2026-04-12_Payment_Chase_INV-2026-010.md"
---

# Odoo Alert — Overdue Invoice INV-2026-010

**Type:** Odoo accounting alert — overdue invoice
**Partner:** Meridian Consulting Group
**Invoice:** INV-2026-010
**Amount:** £2,400.00
**Overdue by:** 31 days
**Received:** 2026-04-11 08:25 UTC

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
