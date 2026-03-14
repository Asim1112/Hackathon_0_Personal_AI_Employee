/**
 * facebook-instagram-mcp/index.js — Gold AI Employee · Facebook & Instagram MCP Server
 *
 * Vault flow:
 *   Claude writes draft  →  /Pending_Approval/FACEBOOK_DRAFT_*.md  (or INSTAGRAM_DRAFT_*.md)
 *   Human reviews draft  →  moves file to /Approved/
 *   THIS SERVER fires    →  posts via Meta Graph API  →  logs to /Done/
 *   On failure           →  logs error note           →  moves to /Rejected/
 *
 * HITL guarantee: nothing is posted unless a human explicitly moves the file
 * to /Approved/. Claude is never able to trigger a post directly.
 *
 * Supported actions (from frontmatter action field):
 *   post_facebook   — post to Facebook Page feed
 *   post_instagram  — post photo to Instagram Business account (requires image_url)
 *
 * Meta Graph API version: v19.0
 * Required permissions: pages_manage_posts, instagram_content_publish
 *
 * Dependencies: node-fetch, chokidar, dotenv, winston
 * Install:      npm install
 * Run:          node index.js
 */

'use strict';

const fs       = require('fs');
const path     = require('path');
const chokidar = require('chokidar');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

// Dynamic import for ESM node-fetch, with CommonJS fetch fallback (Node 18+)
let _fetch;
async function getFetch() {
  if (_fetch) return _fetch;
  if (typeof fetch !== 'undefined') {
    _fetch = fetch;
  } else {
    const mod = await import('node-fetch');
    _fetch = mod.default;
  }
  return _fetch;
}

// ── Config ────────────────────────────────────────────────────────────────────

const cfgFile = path.join(__dirname, 'mcp.json');
const cfg     = fs.existsSync(cfgFile) ? JSON.parse(fs.readFileSync(cfgFile, 'utf8')) : {};

const VAULT          = path.resolve(__dirname, cfg.vault_path || '../..');
const DRY            = cfg.dry_run ?? (process.env.DRY_RUN === 'true');
const GRAPH_BASE     = 'https://graph.facebook.com/v19.0';
const PAGE_ID        = process.env.FACEBOOK_PAGE_ID        || '';
const PAGE_TOKEN     = process.env.FACEBOOK_ACCESS_TOKEN   || '';
const IG_ACCOUNT_ID  = process.env.INSTAGRAM_ACCOUNT_ID    || '';

// ── Logger ────────────────────────────────────────────────────────────────────

const ts  = () => new Date().toISOString();
const log = (level, msg) => console.log(`${ts()} [fb-ig-mcp] ${String(level).padEnd(5)} ${msg}`);

// ── Graph API helper ──────────────────────────────────────────────────────────

async function graphPost(endpoint, body) {
  const f = await getFetch();
  const params = new URLSearchParams({ access_token: PAGE_TOKEN, ...body });
  const resp = await f(`${GRAPH_BASE}/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });
  const data = await resp.json();
  if (!resp.ok || data.error) {
    const msg = data.error ? data.error.message : `HTTP ${resp.status}`;
    throw new Error(`Graph API error: ${msg}`);
  }
  return data;
}

// ── Frontmatter parser ────────────────────────────────────────────────────────

function parseFrontmatter(src) {
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

function extractActionData(body) {
  const m = body.match(/```json\s*([\s\S]*?)```/);
  if (!m) return null;
  try {
    return JSON.parse(m[1].trim());
  } catch (e) {
    log('WARN', `Failed to parse action JSON: ${e.message}`);
    return null;
  }
}

// ── File move helper ──────────────────────────────────────────────────────────

function moveFile(srcPath, destDir, originalContent, note) {
  const base    = path.basename(srcPath);
  const updated = originalContent.replace(/status: pending/, 'status: done')
    + `\n\n---\n\n**${note}**\n`;
  fs.mkdirSync(path.join(VAULT, destDir), { recursive: true });
  fs.writeFileSync(path.join(VAULT, destDir, base), updated, 'utf8');
  fs.unlinkSync(srcPath);
  log('INFO', `→ ${destDir}/${base}`);
}

// ── Facebook post handler ─────────────────────────────────────────────────────

async function handlePostFacebook(data, filePath, rawContent) {
  const base = path.basename(filePath);

  if (!PAGE_ID || !PAGE_TOKEN) {
    log('ERR', 'FACEBOOK_PAGE_ID or FACEBOOK_ACCESS_TOKEN not set');
    moveFile(filePath, 'Rejected', rawContent, 'Missing Facebook credentials');
    return;
  }

  if (DRY) {
    log('DRY', `Would post to Facebook Page ${PAGE_ID}:`);
    log('DRY', `  Message: ${String(data.message || '').slice(0, 100)}`);
    if (data.link) log('DRY', `  Link: ${data.link}`);
    moveFile(filePath, 'Done', rawContent, `DRY RUN — FB post NOT published (${ts()})`);
    return;
  }

  try {
    const body = { message: data.message || '' };
    if (data.link) body.link = data.link;

    const result = await graphPost(`${PAGE_ID}/feed`, body);
    log('OK', `Facebook post published — id: ${result.id}`);
    moveFile(filePath, 'Done', rawContent,
      `Facebook post published ${ts()} · post id: ${result.id}`);
  } catch (err) {
    log('ERR', `Facebook post failed for ${base}: ${err.message}`);
    moveFile(filePath, 'Rejected', rawContent,
      `FB POST FAILED ${ts()} · ${err.message}`);
  }
}

// ── Instagram post handler ────────────────────────────────────────────────────

async function handlePostInstagram(data, filePath, rawContent) {
  const base = path.basename(filePath);

  if (!IG_ACCOUNT_ID || !PAGE_TOKEN) {
    log('ERR', 'INSTAGRAM_ACCOUNT_ID or FACEBOOK_ACCESS_TOKEN not set');
    moveFile(filePath, 'Rejected', rawContent, 'Missing Instagram credentials');
    return;
  }

  if (!data.image_url) {
    log('WARN', `No image_url in ${base} — Instagram requires an image`);
    moveFile(filePath, 'Rejected', rawContent,
      'Instagram post rejected: image_url is required but was not provided');
    return;
  }

  if (DRY) {
    log('DRY', `Would post to Instagram account ${IG_ACCOUNT_ID}:`);
    log('DRY', `  Caption: ${String(data.caption || '').slice(0, 100)}`);
    log('DRY', `  Image:   ${data.image_url}`);
    moveFile(filePath, 'Done', rawContent, `DRY RUN — IG post NOT published (${ts()})`);
    return;
  }

  try {
    // Step 1: Create media container
    const container = await graphPost(`${IG_ACCOUNT_ID}/media`, {
      image_url:   data.image_url,
      caption:     data.caption || '',
    });
    log('INFO', `Instagram media container created — id: ${container.id}`);

    // Step 2: Publish the container
    const publish = await graphPost(`${IG_ACCOUNT_ID}/media_publish`, {
      creation_id: container.id,
    });
    log('OK', `Instagram post published — id: ${publish.id}`);
    moveFile(filePath, 'Done', rawContent,
      `Instagram post published ${ts()} · post id: ${publish.id}`);

  } catch (err) {
    log('ERR', `Instagram post failed for ${base}: ${err.message}`);
    moveFile(filePath, 'Rejected', rawContent,
      `IG POST FAILED ${ts()} · ${err.message}`);
  }
}

// ── Main dispatcher ───────────────────────────────────────────────────────────

async function processApproved(filePath) {
  const base = path.basename(filePath);
  let rawContent;
  try {
    rawContent = fs.readFileSync(filePath, 'utf8');
  } catch (e) {
    log('WARN', `Cannot read ${base}: ${e.message}`);
    return;
  }

  const { meta, body } = parseFrontmatter(rawContent);

  if (meta.type !== 'social_post' || meta.send_via_mcp !== 'facebook-instagram-mcp') {
    log('INFO', `Skip ${base} (type=${meta.type || '?'}, mcp=${meta.send_via_mcp || '?'})`);
    return;
  }

  const action = meta.action || '';
  log('INFO', `Processing ${base} — action: ${action}`);

  const data = extractActionData(body);
  if (!data) {
    log('WARN', `No action JSON found in ${base}`);
    moveFile(filePath, 'Rejected', rawContent, 'No action data JSON found in file body');
    return;
  }

  if (action === 'post_facebook') {
    await handlePostFacebook(data, filePath, rawContent);
  } else if (action === 'post_instagram') {
    await handlePostInstagram(data, filePath, rawContent);
  } else {
    log('WARN', `Unknown action: ${action}`);
    moveFile(filePath, 'Rejected', rawContent, `Unknown action: ${action}`);
  }
}

// ── Startup ───────────────────────────────────────────────────────────────────

if (!PAGE_TOKEN) {
  log('ERR', 'FACEBOOK_ACCESS_TOKEN not set — check .env');
  process.exit(1);
}

for (const d of ['Approved', 'Done', 'Rejected'].map(n => path.join(VAULT, n)))
  fs.mkdirSync(d, { recursive: true });

log('INFO', `Gold AI Employee · Facebook & Instagram MCP Server${DRY ? ' [DRY RUN]' : ''}`);
log('INFO', `Vault     : ${VAULT}`);
log('INFO', `FB Page   : ${PAGE_ID || '(not set)'}`);
log('INFO', `IG Account: ${IG_ACCOUNT_ID || '(not set)'}`);
log('INFO', `Flow: FACEBOOK_DRAFT_*.md / INSTAGRAM_DRAFT_*.md → /Approved (human) → published → /Done`);

chokidar.watch(path.join(VAULT, 'Approved', '*.md'), {
  persistent: true,
  ignoreInitial: false,
  awaitWriteFinish: { stabilityThreshold: 400, pollInterval: 100 },
})
  .on('add',   fp => processApproved(fp).catch(e => log('ERR', e.message)))
  .on('error', e  => log('ERR', `Watcher: ${e.message}`));

log('INFO', 'Watching /Approved — waiting for approved FB/IG post drafts…');
