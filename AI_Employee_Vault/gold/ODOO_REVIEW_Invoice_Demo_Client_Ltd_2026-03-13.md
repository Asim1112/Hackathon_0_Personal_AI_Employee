---
type: odoo_action
action: create_invoice
send_via_mcp: odoo-mcp
status: pending
created: 2026-03-13T10:00:00Z
client: Demo Client Ltd
amount_total: £1500.00
logged: true
---

## Odoo Action: Create Invoice — Demo Client Ltd

**Client:** Demo Client Ltd
**Date:** 2026-03-13
**Reference:** PROJECT-001

### Invoice Lines

| # | Description | Qty | Unit Price | Total |
|---|-------------|-----|-----------|-------|
| 1 | AI Consulting | 10 | £150.00 | £1,500.00 |

**Invoice Total: £1,500.00 (net) / £1,800.00 (incl. 20% VAT)**

### Why This Invoice

This invoice covers AI Consulting services rendered under project reference PROJECT-001 at the standard rate of £150/hr for 10 hours, as defined in `Business_Goals.md` Service Rate Card.

### Action Data

```json
{
  "partner_name": "Demo Client Ltd",
  "partner_email": "",
  "invoice_date": "2026-03-13",
  "lines": [
    { "name": "AI Consulting", "quantity": 10, "price_unit": 150 }
  ],
  "ref": "PROJECT-001"
}
```

> ⚠️ **Human approval required.**
> Move this file to `/Approved/` to create the draft invoice in Odoo.
> The `odoo-mcp` server will create it in **draft** state — you must then
> open Odoo to review and post it manually (or create a `confirm_invoice` action).
