---
type: odoo_action
platform: odoo
send_via_mcp: odoo-mcp
action: create_invoice
created: 2026-03-26T09:48:00Z
status: pending
client: "Meridian Consulting Group"
amount_total: 2400.00
expires: 2026-03-27T09:48:00Z
logged: false
---

# Odoo Action: Create Invoice — Meridian Consulting Group (INV-2026-010)

> ⚠️ **HITL Required — Invoice creation requires human approval.**
> Move this file to `Approved/` to create the draft invoice in Odoo via odoo-mcp.
> The MCP will create it in **draft** state — you must then open Odoo to review and post it manually.

---

## Invoice Summary

**Client:** Meridian Consulting Group
**Reference:** INV-2026-010
**Date:** 2026-02-24 (original due date; invoice is 31 days overdue)
**Payment Terms:** Net 30 days

### Invoice Lines

| # | Description | Qty | Unit Price | Total |
|---|-------------|-----|-----------|-------|
| 1 | AI Strategy Consulting — February 2026 | 1 | £2,400.00 | £2,400.00 |

**Invoice Total: £2,400.00**

### Why This Invoice

Invoice INV-2026-010 was flagged by the Odoo watcher as overdue by 31 days (due 2026-02-24, no payment received). This action creates the invoice record in Odoo draft state so it can be formally posted and included in accounts receivable. A separate payment chase email is in `Inbox/DRAFT_REPLY_Overdue_Invoice_Meridian_Consulting_2026-03-26.md`.

> ⚠️ **Financial Flag:** This is a £2,400 action — above the £50 HITL threshold. Dual check: confirm this invoice has not already been created in Odoo under a different reference before approving.

## Action Data

```json
{
  "partner_name": "Meridian Consulting Group",
  "invoice_date": "2026-02-24",
  "lines": [
    {
      "name": "AI Strategy Consulting — February 2026",
      "quantity": 1,
      "price_unit": 2400.00
    }
  ],
  "ref": "INV-2026-010"
}
```

> Move this file to `/Approved/` to create the draft invoice in Odoo.
> After creation: open Odoo → review → post invoice → send to client.
> Then approve the payment chase email in `Inbox/` to send the reminder.

---

## Next Steps After Approval

1. `odoo-mcp` creates draft invoice in Odoo
2. Open Odoo at http://localhost:8069 → Accounting → Invoices → find draft
3. Review and post the invoice (assigns invoice number)
4. Approve `Inbox/DRAFT_REPLY_Overdue_Invoice_Meridian_Consulting_2026-03-26.md` to send payment chase email
5. Add Meridian Consulting Group to Key Contacts in `Company_Handbook.md` Section 8

---
*Drafted by SKILL_Odoo_Accounting at 2026-03-26T09:48:00Z*


---

**odoo-mcp:** Invoice created in Odoo (ID: 17) — state: draft — http://localhost:8069/web#model=account.move&id=17 · 2026-03-25T22:30:55.382Z
