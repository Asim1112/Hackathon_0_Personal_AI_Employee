---
type: odoo_action
platform: odoo
send_via_mcp: odoo-mcp
action: create_invoice
created: 2026-04-12T08:25:00Z
status: pending
logged: false
partner: "Meridian Consulting Group"
invoice_ref: "INV-2026-010"
amount: 2400.00
currency: GBP
overdue_days: 47
---

# Odoo Action — Create/Post Invoice INV-2026-010

> **HITL Gate — Human approval required.**
> Invoice amount £2,400 exceeds £50 threshold (Company_Handbook Section 6.1).
> Move to `Approved/` to trigger odoo-mcp → creates/posts invoice in Odoo.

---

## Invoice Summary

| Field | Value |
|-------|-------|
| **Partner** | Meridian Consulting Group |
| **Invoice Reference** | INV-2026-010 |
| **Service** | AI Strategy Consulting — February 2026 |
| **Amount (ex. VAT)** | £2,400.00 |
| **VAT (20%)** | £480.00 |
| **Total** | £2,880.00 |
| **Payment Terms** | Net 30 days |
| **Original Due Date** | 2026-02-24 |
| **Days Overdue** | **47 days** |
| **Payments Received** | £0.00 — ZERO PAYMENTS |
| **Odoo Draft ID** | 17 (created 2026-03-25 — NOT yet posted) |

---

## Alert Context

This invoice has been in Odoo draft state since 2026-03-25 (18 days ago). It was not posted because no human approved the action. The payment chase email was also drafted on 2026-03-26 but not sent.

This is the SECOND alert cycle for this invoice (first alerted 2026-03-25 as INV-2026-009/INV-2026-010 at 24 days overdue). It is now 47 days overdue — significantly past the Net 30 payment terms.

**Cash flow impact:** £2,400 outstanding against a monthly revenue target of £10,000 — 24% of monthly target unrecovered.

---

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
  ],
  "payment_terms": "Net 30",
  "due_date": "2026-02-24",
  "note": "OVERDUE — 47 days past due date. Immediate payment required."
}
```

---

## Processing Notes

- **Skill applied:** SKILL_Odoo_Accounting
- **Priority:** URGENT — 47 days overdue, zero payments
- **Business rule:** Payment > £50 → HITL required (Section 6.1)
- **VAT:** 20% applicable (UK client, VAT-registered assumption per Section 6.3)
- **Next action after Odoo posting:** Approve payment chase email in `Inbox/DRAFT_REPLY_2026-04-12_Payment_Chase_INV-2026-010.md`
- **Anomaly flag:** Zero payments received — not flagged as anomaly (known outstanding invoice)
- **Action:** Move to `Approved/` → odoo-mcp creates/posts invoice (Odoo draft ID: 17)

---

*Escalated by SKILL_Odoo_Accounting · 2026-04-12T08:25:00Z*
*Expires: 2026-04-13T08:25:00Z*
