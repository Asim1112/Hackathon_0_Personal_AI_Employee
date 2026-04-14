---
type: odoo_action
platform: odoo
send_via_mcp: odoo-mcp
action: create_invoice
created: 2026-04-13T08:25:00Z
status: pending
logged: false
---

# Odoo Action — Create Invoice INV-2026-010

**Partner:** Meridian Consulting Group
**Invoice Reference:** INV-2026-010
**Amount:** £2,400.00
**Service Period:** February 2026
**Status:** 31 days overdue (due 2026-02-24)

> ⚠️ Amount exceeds £50 HITL threshold (Section 6.1, Company Handbook). Human approval required before Odoo processes this action.

## Summary

Odoo ERP flagged invoice INV-2026-010 as 31 days overdue. This action will create (or re-confirm) the invoice record in Odoo for Meridian Consulting Group. The payment chase email draft is separately in `Inbox/DRAFT_REPLY_2026-04-13_Payment_Chase_INV-2026-010_Meridian.md` — approve both to initiate full recovery workflow.

## Action Data

```json
{
  "partner_name": "Meridian Consulting Group",
  "lines": [
    {
      "name": "AI Strategy Consulting — February 2026",
      "quantity": 1,
      "price_unit": 2400.00
    }
  ]
}
```


---

**odoo-mcp:** Invoice created in Odoo (ID: 25) — state: draft — http://localhost:8069/web#model=account.move&id=25 · 2026-04-13T19:01:35.042Z
