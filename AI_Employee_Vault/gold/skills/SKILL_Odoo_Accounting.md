# SKILL_Odoo_Accounting — Agent Skill

## Purpose
Process Odoo accounting alerts and draft invoice actions for human approval.
This skill handles `type: odoo_alert` items from `Needs_Action/` and prepares
structured action files for the `odoo-mcp` server.

**You do NOT call Odoo directly.** You write action files to `Pending_Approval/`.
The `odoo-mcp` server executes them ONLY after a human moves them to `Approved/`.

---

## When to Invoke

Invoke this skill when:
- A file in `Needs_Action/` has `type: odoo_alert`
- The user or orchestrator asks to "create an invoice" or "sync accounting"
- A client requests an invoice via email or WhatsApp (triage skill flags it)
- The Weekly CEO Briefing requires accounting data

---

## Inputs Required

Read from the trigger file:
- `partner_name` — customer/client name
- `lines` — invoice line items (description, quantity, unit price)
- `invoice_date` — optional, defaults to today in Odoo
- `ref` — optional customer reference

Also read `Business_Goals.md` for rate card and active projects.

---

## Action: Draft a New Invoice

### When to use
Client owes money, project milestone reached, or user asks to invoice a client.

### What you write

Create `Pending_Approval/ODOO_REVIEW_Invoice_<ClientSlug>_<YYYY-MM-DD>.md`:

```markdown
---
type: odoo_action
action: create_invoice
send_via_mcp: odoo-mcp
status: pending
created: <ISO timestamp>
client: <partner_name>
amount_total: <calculated total>
logged: false
---

## Odoo Action: Create Invoice — <partner_name>

**Client:** <partner_name>
**Date:** <invoice_date or today>
**Reference:** <ref or "—">

### Invoice Lines

| # | Description | Qty | Unit Price | Total |
|---|-------------|-----|-----------|-------|
| 1 | <line 1 name> | <qty> | £<price> | £<total> |
| 2 | <line 2 name> | <qty> | £<price> | £<total> |

**Invoice Total: £<sum>**

### Why This Invoice

<1–2 sentences explaining the context: project milestone, service rendered, etc.>

### Action Data
```json
{
  "partner_name": "<client full name>",
  "partner_email": "<client email if known>",
  "invoice_date": "<YYYY-MM-DD>",
  "lines": [
    { "name": "<description>", "quantity": <n>, "price_unit": <price> }
  ],
  "ref": "<PO or project reference>"
}
```

> ⚠️ **Human approval required.**
> Move this file to `/Approved/` to create the draft invoice in Odoo.
> The `odoo-mcp` server will create it in **draft** state — you must then
> open Odoo to review and post it manually (or create a `confirm_invoice` action).
```

---

## Action: Sync Accounting Data

### When to use
- At the start of the Weekly CEO Briefing
- User asks "what's the current financial position"
- Dashboard shows `Accounting/Current_Month.md` is stale (older than 24h)

### What you write

Create `Pending_Approval/ODOO_REVIEW_Sync_Accounting_<YYYY-MM-DD>.md`:

```markdown
---
type: odoo_action
action: sync_accounting
send_via_mcp: odoo-mcp
status: pending
created: <ISO timestamp>
logged: false
---

## Odoo Action: Sync Accounting Data

This action reads current month's invoice and payment data from Odoo and
writes a summary to `Accounting/Current_Month.md`.

**Read-only — no Odoo records are modified.**

### Action Data
```json
{}
```

> Move this file to `/Approved/` to run the sync.
> `odoo-mcp` will update `Accounting/Current_Month.md` automatically.
```

---

## Action: Confirm (Post) an Invoice

### When to use
Only when explicitly instructed by the user. Posting is irreversible in Odoo.

### What you write

Create `Pending_Approval/ODOO_REVIEW_Confirm_Invoice_<ID>_<YYYY-MM-DD>.md`:

```markdown
---
type: odoo_action
action: confirm_invoice
send_via_mcp: odoo-mcp
status: pending
created: <ISO timestamp>
invoice_id: <number>
logged: false
---

## Odoo Action: Confirm Invoice #<ID>

⚠️ **This action is IRREVERSIBLE.** Posting an invoice in Odoo creates journal
entries and assigns an invoice number. Only approve if you are certain.

**Invoice ID in Odoo:** <invoice_id>
**Context:** <explain which invoice and why it's ready to post>

### Action Data
```json
{
  "invoice_id": <invoice_id>
}
```

> Move to `/Approved/` ONLY if you have verified the invoice in Odoo first.
```

---

## Overdue Invoice Alert Handling

When the `odoo_watcher.py` drops an `ODOO_<date>_overdue_<ref>.md` file in `Needs_Action/`:

1. Read the file — it contains the invoice list
2. For each overdue invoice, check `Company_Handbook.md` chasing policy
3. If chasing email is appropriate, use `SKILL_Gmail_Triage` to draft a payment reminder
4. Write the reminder draft to `Inbox/` (not directly to Pending_Approval)
5. Update the Needs_Action file: `status: processed`, `processed_at: <timestamp>`
6. Move to `Done/`
7. Log to `Logs/YYYY-MM-DD.json`:
   ```json
   {
     "action_type": "odoo_overdue_alert",
     "target": "<invoice ref>",
     "skill_used": "SKILL_Odoo_Accounting",
     "result": "chase_email_drafted"
   }
   ```

---

## Rate Card Reference

Read from `Business_Goals.md` → **Service Rate Card** table for current hourly/daily rates.
Always use the rates from that file — do not invent prices.

---

## After Writing the Action File

1. Update the source `Needs_Action/` file: `status: processed`, `processed_at: <now>`
2. Move it to `Done/`
3. Log the action to `Logs/YYYY-MM-DD.json` with `action_type: odoo_draft_created`
4. Note in `Dashboard.md` → **Pending Approvals** table

---

## What NOT to Do

- ❌ Do NOT call Odoo JSON-RPC directly
- ❌ Do NOT invent invoice amounts — use rates from Business_Goals.md or explicit amounts provided
- ❌ Do NOT confirm/post invoices unless explicitly asked by the user
- ❌ Do NOT send payment chase emails without checking Company_Handbook.md chasing policy
