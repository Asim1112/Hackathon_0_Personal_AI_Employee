# Accounting/

This folder contains financial data synced from **Odoo Community** via the `odoo-mcp` server and `odoo_watcher.py`.

## Subfolders
- `Invoices/` — Invoice tracking files (synced from Odoo `account.move`)
- `Expenses/` — Expense records (synced from Odoo `account.expense`)

## File Naming
- `ACCOUNTING_YYYY-MM.md` — Monthly financial summary
- `INVOICE_<client>_<ref>_<date>.md` — Individual invoice tracking
- `EXPENSE_<category>_<date>.md` — Individual expense records

## Important Rules
- **Claude reads these files** to understand financial state during CEO Briefing
- **Claude does NOT write directly to these files** — `odoo_watcher.py` populates them
- **All Odoo actions (create invoice, post payment) require human approval** via `Pending_Approval/`

## Setup
Odoo integration is implemented in Phase 3. Until then, this folder is empty.
See `mcp_servers/odoo-mcp/` once built.
