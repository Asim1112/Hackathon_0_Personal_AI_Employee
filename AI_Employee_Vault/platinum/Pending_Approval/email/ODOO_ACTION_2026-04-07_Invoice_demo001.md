---
type: odoo_action
send_via_mcp: odoo-mcp
action: create_invoice
platform: odoo
created_by: cloud_agent
created: 2026-04-07T00:00:00Z
status: pending
logged: false
---

## Odoo Action: Create Invoice

Invoice request received from Demo Client (client.demo@gmail.com) on 2026-04-08.
Following a consulting engagement in March, the client has requested an invoice for
5 days of AI strategy consulting at a total agreed amount of £500 GBP.

### Action Data
```json
{
  "partner_name": "Demo Client",
  "partner_email": "client.demo@gmail.com",
  "lines": [
    {"name": "AI Strategy Consulting — March 2026 (5 days)", "quantity": 5, "price_unit": 100.00}
  ],
  "currency": "GBP",
  "reference": "demo-invoice-001"
}
```

---
*Draft created by Cloud Agent — awaiting Local Agent approval before creating in Odoo*
