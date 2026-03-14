/**
 * odoo-mcp/index.js — Gold AI Employee · Odoo MCP Server
 *
 * Vault flow:
 *   Claude drafts action  →  /Pending_Approval/ODOO_REVIEW_*.md
 *   Human reviews         →  moves file to /Approved/
 *   THIS SERVER fires     →  calls Odoo JSON-RPC  →  logs to /Done/
 *   On failure            →  logs error note       →  moves to /Rejected/
 *
 * HITL guarantee: Odoo is NEVER modified unless a human explicitly moves
 * the file to /Approved/. Claude writes drafts only — this server executes.
 *
 * Supported actions (set via frontmatter field  action: <type>):
 *   create_invoice   — Create a draft customer invoice in Odoo
 *   confirm_invoice  — Post a draft invoice (creates journal entries)
 *   sync_accounting  — Export current Odoo data → Accounting/Current_Month.md
 *
 * Approval file format (written by SKILL_Odoo_Accounting to Pending_Approval/):
 *   ---
 *   type: odoo_action
 *   action: create_invoice
 *   send_via_mcp: odoo-mcp
 *   status: pending
 *   created: <ISO timestamp>
 *   ---
 *   ## Odoo Action: Create Invoice
 *   ...description...
 *   ### Action Data
 *   ```json
 *   { "partner_name": "...", "lines": [...], ... }
 *   ```
 *
 * Config: vault-root .env  (two levels up: mcp_servers/odoo-mcp/ → gold/)
 * Startup: node index.js
 * Dry-run: DRY_RUN=true node index.js
 *
 * Dependencies: chokidar, dotenv, winston  (+ odoo-client.js local)
 * Install:      npm install
 */

'use strict';

// ── Load env from vault-root .env ─────────────────────────────────────────────
require('dotenv').config({ path: require('path').join(__dirname, '../../.env') });

const fs         = require('fs');
const path       = require('path');
const chokidar   = require('chokidar');
const winston    = require('winston');
const OdooClient = require('./odoo-client');

// ── Logger ────────────────────────────────────────────────────────────────────

const log = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DDTHH:mm:ssZ' }),
    winston.format.printf(({ timestamp, level, message }) =>
      `${timestamp} [odoo-mcp] ${level.toUpperCase().padEnd(7)} ${message}`)
  ),
  transports: [new winston.transports.Console()],
});

// ── Configuration ─────────────────────────────────────────────────────────────

// Vault path derived from file location — never trust env var placeholder
const VAULT       = path.resolve(__dirname, '../..');
const APPROVED    = path.join(VAULT, 'Approved');
const DONE        = path.join(VAULT, 'Done');
const REJECTED    = path.join(VAULT, 'Rejected');
const ACCOUNTING  = path.join(VAULT, 'Accounting');

const DRY_RUN     = process.env.DRY_RUN === 'true';

const odoo = new OdooClient({
  url:      process.env.ODOO_URL      || 'http://localhost:8069',
  db:       process.env.ODOO_DB       || 'ai_employee',
  username: process.env.ODOO_USERNAME || 'admin@example.com',
  password: process.env.ODOO_PASSWORD || 'admin',
});

// ── Markdown helpers ──────────────────────────────────────────────────────────

/** Parse YAML frontmatter from a markdown file. */
function parseFrontmatter(src) {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!m) return { meta: {}, body: src };
  const meta = Object.fromEntries(
    m[1].split('\n').flatMap(line => {
      const kv = line.match(/^([\w_-]+):\s*"?(.+?)"?\s*$/);
      return kv ? [[kv[1], kv[2].trim()]] : [];
    })
  );
  return { meta, body: m[2] };
}

/**
 * Extract the first ```json ... ``` block from a markdown string.
 * Returns a parsed object or throws.
 */
function extractActionData(body) {
  const m = body.match(/```json\s*([\s\S]*?)```/);
  if (!m) throw new Error('No ```json block found in action file — cannot parse action data');
  return JSON.parse(m[1].trim());
}

// ── File lifecycle helpers ────────────────────────────────────────────────────

function moveFile(srcPath, destDir, originalContent, note) {
  const base    = path.basename(srcPath);
  const updated = originalContent + `\n\n---\n\n**odoo-mcp:** ${note} · ${new Date().toISOString()}\n`;
  fs.writeFileSync(path.join(destDir, base), updated, 'utf8');
  fs.unlinkSync(srcPath);
  log.info(`→ ${path.basename(destDir)}/${base}`);
}

// ── Action handlers ───────────────────────────────────────────────────────────

/**
 * create_invoice — Create a draft customer invoice in Odoo.
 *
 * Required fields in action data JSON:
 *   partner_name   {string}  Customer name
 *   lines          {Array}   [{name, quantity, price_unit}]
 *
 * Optional fields:
 *   partner_email  {string}  Used when creating a new partner
 *   invoice_date   {string}  YYYY-MM-DD
 *   invoice_date_due {string} YYYY-MM-DD
 *   ref            {string}  Customer PO reference
 */
async function handleCreateInvoice(data, filePath, rawContent) {
  const { partner_name, partner_email, lines, invoice_date, invoice_date_due, ref } = data;

  if (!partner_name) throw new Error('action data missing required field: partner_name');
  if (!lines || !lines.length) throw new Error('action data missing required field: lines');

  log.info(`  Customer : ${partner_name}`);
  log.info(`  Lines    : ${lines.length} line(s)`);
  lines.forEach((l, i) => log.info(`    [${i + 1}] ${l.name} × ${l.quantity || 1} @ ${l.price_unit}`));

  if (DRY_RUN) {
    log.info('  [DRY RUN] Would create invoice in Odoo — skipping API call');
    moveFile(filePath, DONE, rawContent, 'DRY RUN — invoice NOT created');
    return;
  }

  const invoiceId = await odoo.createInvoiceDraft({
    partnerName:    partner_name,
    partnerEmail:   partner_email,
    lines,
    invoiceDate:    invoice_date,
    invoiceDateDue: invoice_date_due,
    ref,
  });

  const odooLink = `${process.env.ODOO_URL || 'http://localhost:8069'}/web#model=account.move&id=${invoiceId}`;
  log.info(`  ✅ Invoice created — Odoo ID: ${invoiceId}`);
  log.info(`  Link: ${odooLink}`);

  moveFile(filePath, DONE, rawContent,
    `Invoice created in Odoo (ID: ${invoiceId}) — state: draft — ${odooLink}`);
}

/**
 * confirm_invoice — Post a draft invoice (assigns invoice number + creates journal entries).
 *
 * Required fields in action data JSON:
 *   invoice_id  {number}  Odoo account.move record ID
 *
 * Note: This is a significant accounting action. Odoo will reject it if the invoice
 * is already posted or has validation errors (missing accounts, etc.)
 */
async function handleConfirmInvoice(data, filePath, rawContent) {
  const { invoice_id } = data;

  if (!invoice_id) throw new Error('action data missing required field: invoice_id');

  log.info(`  Invoice ID : ${invoice_id}`);

  if (DRY_RUN) {
    log.info('  [DRY RUN] Would confirm/post invoice in Odoo — skipping API call');
    moveFile(filePath, DONE, rawContent, `DRY RUN — invoice ID ${invoice_id} NOT posted`);
    return;
  }

  await odoo.confirmInvoice(invoice_id);
  const odooLink = `${process.env.ODOO_URL || 'http://localhost:8069'}/web#model=account.move&id=${invoice_id}`;
  log.info(`  ✅ Invoice ID ${invoice_id} confirmed (state: posted)`);

  moveFile(filePath, DONE, rawContent,
    `Invoice ID ${invoice_id} posted in Odoo (state: posted) — ${odooLink}`);
}

/**
 * sync_accounting — Query Odoo and write current month's data to Accounting/Current_Month.md.
 * No Odoo write — this is a read-only sync. Can be approved anytime to refresh the vault.
 */
async function handleSyncAccounting(data, filePath, rawContent) {
  const now   = new Date();
  const year  = now.getFullYear();
  const month = now.getMonth() + 1;

  log.info(`  Syncing Odoo data for ${year}-${String(month).padStart(2, '0')}…`);

  if (DRY_RUN) {
    log.info('  [DRY RUN] Would sync Odoo accounting data — skipping');
    moveFile(filePath, DONE, rawContent, 'DRY RUN — accounting sync skipped');
    return;
  }

  const summary  = await odoo.getMonthlySummary(year, month);
  const overdue  = await odoo.getOverdueInvoices();
  const syncedAt = now.toISOString();

  // Build markdown content for Accounting/Current_Month.md
  const invoiceRows = summary.invoices.map(inv => {
    const partner = Array.isArray(inv.partner_id) ? inv.partner_id[1] : inv.partner_id;
    const due     = inv.invoice_date_due || '—';
    const status  = inv.payment_state === 'paid' ? '✅ Paid' : `⏳ ${inv.payment_state}`;
    return `| ${inv.name} | ${partner} | £${inv.amount_total.toFixed(2)} | ${due} | ${status} |`;
  }).join('\n') || '| — No invoices this month — | — | — | — | — |';

  const overdueRows = overdue.map(inv => {
    const partner    = Array.isArray(inv.partner_id) ? inv.partner_id[1] : inv.partner_id;
    const daysOverdue = Math.floor((Date.now() - new Date(inv.invoice_date_due)) / 86400000);
    return `| ${inv.name} | ${partner} | £${inv.amount_residual.toFixed(2)} | ${inv.invoice_date_due} | **${daysOverdue} days** |`;
  }).join('\n') || '| — No overdue invoices ✅ — | — | — | — | — |';

  const mdContent = `---
type: accounting_summary
period: ${year}-${String(month).padStart(2, '0')}
updated: ${syncedAt}
updated_by: odoo-mcp
source: odoo
---

# Monthly Accounting Summary — ${now.toLocaleString('default', { month: 'long' })} ${year}

> Synced from Odoo Community via \`odoo-mcp\` (sync_accounting action).
> Last sync: ${syncedAt}

---

## Revenue Summary

| Metric | Value |
|--------|-------|
| Invoices this month | ${summary.invoiceCount} |
| Total Revenue | £${summary.totalRevenue.toFixed(2)} |
| Collected | £${summary.collected.toFixed(2)} |
| Outstanding | £${summary.outstanding.toFixed(2)} |

---

## Invoices This Month

| Invoice # | Customer | Amount | Due Date | Status |
|-----------|----------|--------|----------|--------|
${invoiceRows}

---

## Overdue Invoices

| Invoice # | Customer | Amount Due | Due Date | Overdue |
|-----------|----------|------------|----------|---------|
${overdueRows}

---

*Synced by odoo-mcp — ${syncedAt}*
`;

  fs.mkdirSync(ACCOUNTING, { recursive: true });
  fs.writeFileSync(path.join(ACCOUNTING, 'Current_Month.md'), mdContent, 'utf8');
  log.info(`  ✅ Accounting/Current_Month.md updated`);
  log.info(`     Revenue: £${summary.totalRevenue.toFixed(2)} | Outstanding: £${summary.outstanding.toFixed(2)} | Overdue invoices: ${overdue.length}`);

  moveFile(filePath, DONE, rawContent,
    `Accounting sync complete — Revenue: £${summary.totalRevenue.toFixed(2)}, Outstanding: £${summary.outstanding.toFixed(2)}, Overdue: ${overdue.length}`);
}

// ── Main processor ────────────────────────────────────────────────────────────

async function processApproved(filePath) {
  const base       = path.basename(filePath);
  const rawContent = fs.readFileSync(filePath, 'utf8');
  const { meta, body } = parseFrontmatter(rawContent);

  // Guard: only handle odoo_action files destined for this server
  if (meta.type !== 'odoo_action') {
    log.info(`Skip ${base} (type=${meta.type || '?'} — not odoo_action)`);
    return;
  }
  if (meta.send_via_mcp !== 'odoo-mcp') {
    log.info(`Skip ${base} (send_via_mcp=${meta.send_via_mcp || '?'} — not odoo-mcp)`);
    return;
  }

  const action = meta.action || (extractActionDataSafe(body) || {}).action;

  log.info(`Processing: ${base} | action: ${action}`);

  try {
    let data = {};
    try { data = extractActionData(body); } catch { /* action may not need extra data */ }

    switch (action) {
      case 'create_invoice':
        await handleCreateInvoice(data, filePath, rawContent);
        break;
      case 'confirm_invoice':
        await handleConfirmInvoice(data, filePath, rawContent);
        break;
      case 'sync_accounting':
        await handleSyncAccounting(data, filePath, rawContent);
        break;
      default:
        throw new Error(`Unknown action: '${action}' — check frontmatter action: field`);
    }
  } catch (err) {
    log.error(`  ❌ Failed: ${err.message}`);
    moveFile(filePath, REJECTED, rawContent, `FAILED: ${err.message}`);
  }
}

function extractActionDataSafe(body) {
  try { return extractActionData(body); } catch { return null; }
}

// ── Startup ───────────────────────────────────────────────────────────────────

async function startup() {
  // Ensure folders exist
  for (const dir of [APPROVED, DONE, REJECTED, ACCOUNTING]) {
    fs.mkdirSync(dir, { recursive: true });
  }

  // Verify Odoo is reachable
  try {
    const version = await odoo.ping();
    log.info(`Odoo reachable — server version: ${version}`);
    // Authenticate once to surface credential errors immediately
    await odoo.authenticate();
    log.info(`Authenticated as uid: ${odoo.uid} (db: ${odoo.db})`);
  } catch (err) {
    log.error(`Cannot connect to Odoo: ${err.message}`);
    log.error(`Check ODOO_URL / ODOO_DB / ODOO_USERNAME / ODOO_PASSWORD in .env`);
    process.exit(1);
  }

  log.info('──────────────────────────────────────────────');
  log.info('Gold AI Employee · Odoo MCP Server' + (DRY_RUN ? ' [DRY RUN]' : ''));
  log.info(`Vault   : ${VAULT}`);
  log.info(`Odoo    : ${process.env.ODOO_URL || 'http://localhost:8069'} / db: ${odoo.db}`);
  log.info('Actions : create_invoice | confirm_invoice | sync_accounting');
  log.info('Flow    : Pending_Approval/ → (human approves) → Approved/ → Odoo → Done/');
  log.info('──────────────────────────────────────────────');

  // Start watching
  chokidar.watch(path.join(APPROVED, '*.md'), {
    persistent:       true,
    ignoreInitial:    false,
    awaitWriteFinish: { stabilityThreshold: 500, pollInterval: 100 },
  })
    .on('add',   fp => processApproved(fp).catch(e => log.error(`Unhandled: ${e.message}`)))
    .on('error', e  => log.error(`Watcher error: ${e.message}`));

  log.info('Watching /Approved — waiting for approved Odoo actions…');
}

startup();
