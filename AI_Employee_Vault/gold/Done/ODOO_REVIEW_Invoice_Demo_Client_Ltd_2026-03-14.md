---
type: odoo_action
action: create_invoice
send_via_mcp: odoo-mcp
status: pending
created: 2026-03-14T10:30:00Z
client: "Demo Client Ltd"
amount_total: 1800.00
logged: false
---

## Odoo Action: Create Invoice — Demo Client Ltd

**Client:** Demo Client Ltd
**Date:** 2026-03-14
**Reference:** PROJECT-001

### Invoice Lines

| # | Description | Qty | Unit Price | Total |
|---|-------------|-----|-----------|-------|
| 1 | AI Consulting | 10 | £150.00 | £1,500.00 |

**Invoice Total (net): £1,500.00**
**VAT (20%): £300.00**
**Invoice Total (incl. VAT): £1,800.00**

### Why This Invoice

AI consulting services (10 hours) rendered for Demo Client Ltd under project reference PROJECT-001. Rate of £150/hr taken from the Service Rate Card in `Business_Goals.md`. Invoice is over the £50 HITL threshold — human approval required before creation in Odoo.

⚠️ **Note:** Partner email for Demo Client Ltd is not known. Please add it to the action data below before approving, or look it up in Odoo.

### Action Data

```json
{
  "partner_name": "Demo Client Ltd",
  "partner_email": "",
  "invoice_date": "2026-03-14",
  "lines": [
    { "name": "AI Consulting", "quantity": 10, "price_unit": 150.00 }
  ],
  "ref": "PROJECT-001"
}
```

> ⚠️ **Human approval required.**
> Move this file to `/Approved/` to create the draft invoice in Odoo.
> The `odoo-mcp` server will create it in **draft** state — you must then
> open Odoo to review and post it manually (or create a `confirm_invoice` action).
>
> **Before approving:** Verify Demo Client Ltd's VAT status and add their partner email above.


---

**odoo-mcp:** Invoice created in Odoo (ID: 12) — state: draft — http://localhost:8069/web#model=account.move&id=12 · 2026-03-13T23:53:06.326Z
