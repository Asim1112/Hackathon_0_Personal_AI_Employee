/**
 * email-mcp/index.js — Silver AI Employee · Email MCP Server
 *
 * Vault flow:
 *   Claude writes draft  →  /Inbox/DRAFT_REPLY_*.md
 *   Human reviews draft  →  moves file to /Approved/
 *   THIS SERVER fires    →  sends via Gmail SMTP  →  logs to /Done/
 *   On failure           →  logs error note       →  moves to /Rejected/
 *
 * HITL guarantee: nothing is sent unless a human explicitly moves the file
 * to /Approved/. Claude is never able to trigger a send directly.
 *
 * Config: mcp.json (takes priority) → environment variables (fallback)
 * Startup: node index.js
 * Dry-run: set dry_run: true in mcp.json or DRY_RUN=true in env
 *
 * Dependencies: nodemailer, chokidar
 * Install:      npm install
 */

'use strict';

const fs         = require('fs');
const path       = require('path');
const nodemailer = require('nodemailer');
const chokidar   = require('chokidar');

// Load credentials from vault-root .env (two levels up: mcp_servers/email-mcp → silver/)
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

// ── Config: mcp.json wins, env vars are fallback ──────────────────────────────

const cfgFile = path.join(__dirname, 'mcp.json');
const cfg     = fs.existsSync(cfgFile) ? JSON.parse(fs.readFileSync(cfgFile, 'utf8')) : {};

// Pin vault path to __dirname — never read VAULT_PATH env var (may be .env placeholder)
// Only mcp.json's vault_path field can override (explicit, trusted config).
const VAULT = path.resolve(__dirname, cfg.vault_path || '../..');
const DRY   = cfg.dry_run  ?? (process.env.DRY_RUN   === 'true');
const FROM  = cfg.from     || process.env.SMTP_FROM   || cfg.smtp_user || process.env.SMTP_USER;
const SMTP  = {
  host:   cfg.smtp_host   || process.env.SMTP_HOST   || 'smtp.gmail.com',
  port:  +cfg.smtp_port   || +process.env.SMTP_PORT  || 587,
  secure: cfg.smtp_secure ?? (process.env.SMTP_SECURE === 'true'),
  auth:  { user: cfg.smtp_user || process.env.SMTP_USER || '',
           pass: cfg.smtp_pass || process.env.SMTP_PASS || '' },
};

// ── Minimal logger ────────────────────────────────────────────────────────────

const ts  = () => new Date().toISOString();
const log = (level, msg) => console.log(`${ts()} [email-mcp] ${level.padEnd(5)} ${msg}`);

// ── Frontmatter + body helpers ────────────────────────────────────────────────

function parseFM(src) {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!m) return { meta: {}, body: src };
  const meta = Object.fromEntries(
    m[1].split('\n').flatMap(l => {
      const kv = l.match(/^([\w_-]+):\s*"?(.+?)"?\s*$/);
      return kv ? [[kv[1], kv[2].trim()]] : [];
    })
  );
  return { meta, body: m[2] };
}

function toPlainText(md) {
  return md
    .replace(/^[>#]+\s*/gm, '')          // strip headings and blockquotes
    .replace(/\*\*(.+?)\*\*/g, '$1')     // strip bold
    .replace(/^\s*[-*]\s+/gm, '• ')      // normalise bullets
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

// ── Core: process one file that appeared in /Approved ────────────────────────

async function processApproved(filePath) {
  const base = path.basename(filePath);
  const raw  = fs.readFileSync(filePath, 'utf8');
  const { meta, body } = parseFM(raw);

  if (meta.type !== 'draft_reply' || meta.send_via_mcp !== 'email-mcp') {
    log('INFO', `Skip ${base} (type=${meta.type || '?'}, mcp=${meta.send_via_mcp || '?'})`);
    return;
  }

  const to      = meta.to;
  const subject = meta.subject || '(no subject)';
  const text    = toPlainText(body);

  if (!to) { log('WARN', `No 'to' field in ${base} — moving to Rejected/`); moveFile(filePath, 'Rejected', raw, `No recipient address`); return; }

  if (DRY) {
    log('DRY', `Would send → To: ${to} | Subject: ${subject}`);
    log('DRY', `Body: ${text.slice(0, 100).replace(/\n/g, ' ')}…`);
    moveFile(filePath, 'Done', raw, `DRY RUN — email NOT sent (${ts()})`);
    return;
  }

  log('INFO', `Sending → To: ${to} | Subject: ${subject}`);
  try {
    const info = await nodemailer.createTransport(SMTP).sendMail({ from: FROM, to, subject, text });
    log('OK   ', `Sent ${base} — msgId: ${info.messageId}`);
    moveFile(filePath, 'Done', raw, `Sent ${ts()} · msgId: ${info.messageId}`);
  } catch (err) {
    log('ERR  ', `Send failed for ${base}: ${err.message}`);
    moveFile(filePath, 'Rejected', raw, `SEND FAILED ${ts()} · ${err.message}`);
  }
}

function moveFile(srcPath, destFolder, originalContent, note) {
  const base    = path.basename(srcPath);
  const updated = originalContent.replace('status: draft', 'status: sent')
    + `\n\n---\n\n**${note}**\n`;
  fs.writeFileSync(path.join(VAULT, destFolder, base), updated, 'utf8');
  fs.unlinkSync(srcPath);
  log('INFO', `→ ${destFolder}/${base}`);
}

// ── Startup ───────────────────────────────────────────────────────────────────

if (!SMTP.auth.user || !SMTP.auth.pass) {
  log('ERR', 'smtp_user / smtp_pass not set — check mcp.json or environment variables');
  process.exit(1);
}

for (const d of ['Approved', 'Inbox', 'Done', 'Rejected'].map(n => path.join(VAULT, n)))
  fs.mkdirSync(d, { recursive: true });

log('INFO', `Silver AI Employee · Email MCP Server${DRY ? ' [DRY RUN MODE]' : ''}`);
log('INFO', `Vault : ${VAULT}`);
log('INFO', `SMTP  : ${SMTP.host}:${SMTP.port} (user: ${SMTP.auth.user})`);
log('INFO', `Flow  : /Inbox (Claude drafts) → /Approved (human approves) → sent → /Done`);

chokidar.watch(path.join(VAULT, 'Approved', '*.md'), {
  persistent: true,
  ignoreInitial: false,
  awaitWriteFinish: { stabilityThreshold: 400, pollInterval: 100 },
})
  .on('add',   fp => processApproved(fp).catch(e => log('ERR', e.message)))
  .on('error', e  => log('ERR', `Watcher: ${e.message}`));

log('INFO', 'Watching /Approved — waiting for approved email drafts…');
