---
type: odoo_action
platform: odoo
send_via_mcp: odoo-mcp
action: create_invoice
created: 2026-04-14T08:35:00Z
status: pending
logged: false
---

# Odoo Action — Create Invoice for Meridian Consulting Group

**Invoice Reference:** INV-2026-010
**Partner:** Meridian Consulting Group
**Amount:** £2,400.00
**Overdue by:** 31 days (due 2026-02-24)

---

## Triage Notes

- Source alert: `ODOO_2026-04-14_overdue_invoice_INV-2026-010.md`
- Amount: £2,400.00 — **exceeds £50 HITL threshold** → mandatory HITL
- Action type: `create_invoice` (record the invoice in Odoo for the overdue amount)
- Payment chase email also drafted → `Inbox/DRAFT_REPLY_2026-04-14_Invoice_Chase_INV-2026-010_Meridian.md`
- Rule: Section 6.1 — any financial action >£50 requires Pending_Approval/ before execution

## Action Data

```json
{
  "partner_name": "Meridian Consulting Group",
  "invoice_ref": "INV-2026-010",
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

*Prepared by SKILL_Odoo_Accounting — 2026-04-14T08:35:00Z*
*HITL required — move to Approved/ to trigger odoo-mcp*
*Also approve the payment chase email draft in Inbox/ to send via email-mcp*


---

**odoo-mcp:** Invoice created in Odoo (ID: 27) — state: draft — http://localhost:8069/web#model=account.move&id=27 · 2026-04-13T20:05:33.325Z
