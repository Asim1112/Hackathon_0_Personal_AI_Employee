---
type: odoo_action
platform: odoo
send_via_mcp: odoo-mcp
action: create_invoice
created: 2026-04-12T09:25:00Z
status: pending
expires: 2026-04-13T09:25:00Z
logged: false
---

# Odoo Action — Create/Confirm Invoice INV-2026-010 · Meridian Consulting Group

> ⚠️ HUMAN REVIEW REQUIRED — Amount: £2,400.00. Exceeds £50 HITL threshold (Section 6.1).
> Do NOT act until this file is moved to Approved/.

**Triggered by:** SKILL_Odoo_Accounting
**Source file:** ODOO_2026-04-12_overdue_invoice_INV-2026-010.md
**Expires:** 2026-04-13T09:25:00Z (24h)

---

## Alert Summary

| Field | Value |
|---|---|
| **Invoice Ref** | INV-2026-010 |
| **Client** | Meridian Consulting Group |
| **Amount** | £2,400.00 |
| **Service** | AI Strategy Consulting — February 2026 |
| **Issue Date** | 2026-02-24 (inferred) |
| **Due Date** | 2026-02-24 (Net 30 — due on issue) |
| **Days Overdue** | **31 days** 🔴 |
| **Payments Received** | None |

**Action required:** Create invoice in Odoo and send payment chase email to Meridian Consulting Group.

---

## Action Data

```json
{
  "action": "create_invoice",
  "partner_name": "Meridian Consulting Group",
  "invoice_ref": "INV-2026-010",
  "lines": [
    {
      "name": "AI Strategy Consulting — February 2026",
      "quantity": 1,
      "price_unit": 2400.00
    }
  ],
  "payment_terms": "Net 30",
  "due_date": "2026-02-24",
  "currency": "GBP",
  "notes": "Invoice overdue by 31 days as at 2026-04-12. Payment chase email drafted — see Inbox/DRAFT_REPLY_2026-04-12_Payment_Chase_INV-2026-010_Meridian.md."
}
```

---

## Companion Actions

Also review and approve:
- **Payment chase email:** `Inbox/DRAFT_REPLY_2026-04-12_Payment_Chase_INV-2026-010_Meridian.md`
  → Move to `Approved/` to trigger `email-mcp` to send the overdue payment reminder to Meridian

---

## Approval Instructions

1. Move this file to `Approved/` → `odoo-mcp` will create the invoice record in Odoo
2. Move the payment chase email (above) to `Approved/` → `email-mcp` will send the reminder
3. After payment is received, record manually in Odoo — do NOT auto-record payments

---
*Written by SKILL_Odoo_Accounting at 2026-04-12T09:25:00Z*
