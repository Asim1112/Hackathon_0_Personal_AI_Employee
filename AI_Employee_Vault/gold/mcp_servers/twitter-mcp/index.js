/**
 * twitter-mcp/index.js — Gold AI Employee · Twitter/X MCP Server
 *
 * Vault flow:
 *   Claude writes draft  →  /Pending_Approval/TWITTER_DRAFT_*.md
 *   Human reviews draft  →  moves file to /Approved/
 *   THIS SERVER fires    →  posts via Twitter API v2  →  logs to /Done/
 *   On failure           →  logs error note           →  moves to /Rejected/
 *
 * HITL guarantee: nothing is posted unless a human explicitly moves the file
 * to /Approved/. Claude is never able to trigger a post directly.
 *
 * Supported actions (from frontmatter action field):
 *   post_tweet   — single tweet or thread
 *
 * Dependencies: twitter-api-v2, chokidar, dotenv, winston
 * Install:      npm install
 * Run:          node index.js
 */

'use strict';

const fs       = require('fs');
const path     = require('path');
const chokidar = require('chokidar');
const { TwitterApi } = require('twitter-api-v2');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

// ── Config ────────────────────────────────────────────────────────────────────

const cfgFile = path.join(__dirname, 'mcp.json');
const cfg     = fs.existsSync(cfgFile) ? JSON.parse(fs.readFileSync(cfgFile, 'utf8')) : {};

const VAULT = path.resolve(__dirname, cfg.vault_path || '../..');
const DRY   = cfg.dry_run ?? (process.env.DRY_RUN === 'true');

// ── Logger ────────────────────────────────────────────────────────────────────

const ts  = () => new Date().toISOString();
const log = (level, msg) => console.log(`${ts()} [twitter-mcp] ${String(level).padEnd(5)} ${msg}`);

// ── Twitter client ────────────────────────────────────────────────────────────

function createTwitterClient() {
  const apiKey       = process.env.TWITTER_API_KEY;
  const apiSecret    = process.env.TWITTER_API_SECRET;
  const accessToken  = process.env.TWITTER_ACCESS_TOKEN;
  const accessSecret = process.env.TWITTER_ACCESS_TOKEN_SECRET;

  if (!apiKey || !apiSecret || !accessToken || !accessSecret) {
    log('ERR', 'Missing Twitter credentials — set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET in .env');
    process.exit(1);
  }

  return new TwitterApi({
    appKey:          apiKey,
    appSecret:       apiSecret,
    accessToken:     accessToken,
    accessSecret:    accessSecret,
  }).readWrite;
}

const twitterClient = DRY ? null : createTwitterClient();

// ── Frontmatter parser (same pattern as email-mcp) ───────────────────────────

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

// ── Extract action JSON from markdown body ────────────────────────────────────

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

// ── Post tweet (single or thread) ────────────────────────────────────────────

async function handlePostTweet(data, filePath, rawContent) {
  const base = path.basename(filePath);

  if (DRY) {
    if (data.thread && data.thread.length) {
      log('DRY', `Would post thread (${data.thread.length} tweets):`);
      data.thread.forEach((t, i) => log('DRY', `  [${i + 1}] ${t.slice(0, 80)}`));
    } else {
      log('DRY', `Would tweet: ${String(data.content || '').slice(0, 100)}`);
    }
    moveFile(filePath, 'Done', rawContent, `DRY RUN — tweet NOT posted (${ts()})`);
    return;
  }

  try {
    if (data.thread && data.thread.length > 1) {
      // Post a thread
      let replyToId = null;
      const tweetIds = [];
      for (const text of data.thread) {
        const params = { text };
        if (replyToId) params.reply = { in_reply_to_tweet_id: replyToId };
        const resp = await twitterClient.v2.tweet(params);
        replyToId = resp.data.id;
        tweetIds.push(replyToId);
        log('OK', `Thread tweet posted — id: ${replyToId}`);
      }
      moveFile(filePath, 'Done', rawContent,
        `Thread posted ${ts()} · ${tweetIds.length} tweets · first id: ${tweetIds[0]}`);

    } else {
      // Single tweet
      const text = data.content || (data.thread && data.thread[0]) || '';
      if (!text) {
        log('WARN', `No tweet content in ${base}`);
        moveFile(filePath, 'Rejected', rawContent, `No tweet content found`);
        return;
      }
      const resp = await twitterClient.v2.tweet({ text });
      const tweetId = resp.data.id;
      log('OK', `Tweet posted — id: ${tweetId}`);
      moveFile(filePath, 'Done', rawContent, `Tweet posted ${ts()} · id: ${tweetId}`);
    }
  } catch (err) {
    log('ERR', `Post failed for ${base}: ${err.message}`);
    moveFile(filePath, 'Rejected', rawContent, `POST FAILED ${ts()} · ${err.message}`);
  }
}

// ── Reply to tweet ────────────────────────────────────────────────────────────

async function handleReplyTweet(data, filePath, rawContent) {
  const base = path.basename(filePath);
  const replyToId = data.reply_to_tweet_id;
  const text      = data.content || '';

  if (!replyToId) {
    log('WARN', `Missing reply_to_tweet_id in ${base}`);
    moveFile(filePath, 'Rejected', rawContent, `Missing reply_to_tweet_id in action JSON`);
    return;
  }
  if (!text) {
    log('WARN', `No reply content in ${base}`);
    moveFile(filePath, 'Rejected', rawContent, `No reply content found in action JSON`);
    return;
  }

  if (DRY) {
    log('DRY', `Would reply to tweet ${replyToId}: ${text.slice(0, 100)}`);
    moveFile(filePath, 'Done', rawContent, `DRY RUN — reply NOT posted (${ts()})`);
    return;
  }

  try {
    const resp = await twitterClient.v2.tweet({
      text,
      reply: { in_reply_to_tweet_id: replyToId },
    });
    const tweetId = resp.data.id;
    log('OK', `Reply posted — id: ${tweetId}, in_reply_to: ${replyToId}`);
    moveFile(filePath, 'Done', rawContent,
      `Reply posted ${ts()} · id: ${tweetId} · in_reply_to: ${replyToId}`);
  } catch (err) {
    log('ERR', `Reply failed for ${base}: ${err.message}`);
    moveFile(filePath, 'Rejected', rawContent, `REPLY FAILED ${ts()} · ${err.message}`);
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

  // Only handle social_post/social_draft files intended for this server
  if ((meta.type !== 'social_post' && meta.type !== 'social_draft') || meta.send_via_mcp !== 'twitter-mcp') {
    log('INFO', `Skip ${base} (type=${meta.type || '?'}, mcp=${meta.send_via_mcp || '?'})`);
    return;
  }

  // Resolve action: prefer frontmatter action, fall back to content_type, then default
  const action = meta.action || (meta.content_type === 'reply' ? 'reply_tweet' : 'post_tweet');
  log('INFO', `Processing ${base} — action: ${action}`);

  const data = extractActionData(body);
  if (!data) {
    log('WARN', `No action JSON found in ${base}`);
    moveFile(filePath, 'Rejected', rawContent, `No action data JSON found in file body`);
    return;
  }

  if (action === 'post_tweet') {
    await handlePostTweet(data, filePath, rawContent);
  } else if (action === 'reply_tweet') {
    await handleReplyTweet(data, filePath, rawContent);
  } else {
    log('WARN', `Unknown action: ${action}`);
    moveFile(filePath, 'Rejected', rawContent, `Unknown action: ${action}`);
  }
}

// ── Startup ───────────────────────────────────────────────────────────────────

for (const d of ['Approved', 'Done', 'Rejected'].map(n => path.join(VAULT, n)))
  fs.mkdirSync(d, { recursive: true });

log('INFO', `Gold AI Employee · Twitter MCP Server${DRY ? ' [DRY RUN]' : ''}`);
log('INFO', `Vault: ${VAULT}`);
log('INFO', `Flow: TWITTER_DRAFT_*.md → /Approved (human) → posted → /Done`);

chokidar.watch(path.join(VAULT, 'Approved', '*.md'), {
  persistent: true,
  ignoreInitial: false,
  awaitWriteFinish: { stabilityThreshold: 400, pollInterval: 100 },
})
  .on('add',   fp => processApproved(fp).catch(e => log('ERR', e.message)))
  .on('error', e  => log('ERR', `Watcher: ${e.message}`));

log('INFO', 'Watching /Approved — waiting for approved tweet drafts…');
