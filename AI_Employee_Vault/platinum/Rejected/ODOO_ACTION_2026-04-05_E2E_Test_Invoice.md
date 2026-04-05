---
type: odoo_action
send_via_mcp: odoo-mcp
action: create_invoice
platform: odoo
created_by: cloud_agent
created: 2026-04-05T10:10:00Z
status: pending
logged: false
---

## Odoo Action: Create Invoice

E2E test invoice — verifying odoo-mcp -> Odoo Community integration.

### Action Data
{
  "partner_name": "E2E Test Client",
  "lines": [
    {"name": "AI Employee Platinum Service", "quantity": 1, "price_unit": 100.00}
  ]
}

---

**odoo-mcp:** FAILED: action data missing required field: partner_name · 2026-04-05T11:45:49.341Z
