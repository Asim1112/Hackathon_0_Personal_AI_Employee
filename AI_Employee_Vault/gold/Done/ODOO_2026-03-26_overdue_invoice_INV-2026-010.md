---
type: odoo_alert
status: processed
processed_at: 2026-03-26T09:50:00Z
platform: odoo
action_hint: create_invoice
partner: "Meridian Consulting Group"
invoice_ref: "INV-2026-010"
amount_due: 2400.00
currency: GBP
overdue_days: 31
received: 2026-03-26T08:25:00Z
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
**Received:** 2026-03-26 08:25 UTC

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

**IMPORTANT:** Use ONLY `action: create_invoice` — do NOT use payment_chase or any other action.
