/**
 * linkedin-mcp/index.js
 * Silver-tier AI Employee — LinkedIn MCP Server
 *
 * Watches the /Approved folder for approved LinkedIn draft files (type: linkedin_draft).
 * When a human moves a draft from /Pending_Approval to /Approved, this server:
 *   1. Reads the draft content
 *   2. Logs into LinkedIn via Playwright (browser automation)
 *   3. Creates a new post with the approved content
 *   4. Logs the result and moves the file to /Done
 *
 * HITL guarantee: This server NEVER posts unless a human has explicitly moved
 * the draft file to /Approved. Claude writes drafts only — this server posts.
 *
 * Setup:
 *   1. Copy .env.example to .env and fill in credentials
 *   2. npm install && npm run install-browser
 *   3. node index.js
 *
 * Note: LinkedIn may require a CAPTCHA or SMS verification on first login.
 * Set HEADLESS=false in .env to see the browser window and complete verification.
 */

'use strict';

// Load credentials from vault-root .env (two levels up: mcp_servers/linkedin-mcp → silver/)
// Using explicit path so this works regardless of which directory node is run from.
require('dotenv').config({ path: require('path').join(__dirname, '../../.env') });

const { chromium } = require('playwright');
const chokidar     = require('chokidar');
const winston      = require('winston');
const fs           = require('fs');
const path         = require('path');

// ---------------------------------------------------------------------------
// Logger
// ---------------------------------------------------------------------------

const log = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DDTHH:mm:ssZ' }),
    winston.format.printf(({ timestamp, level, message }) =>
      `${timestamp} [linkedin-mcp] ${level.toUpperCase().padEnd(7)} ${message}`)
  ),
  transports: [new winston.transports.Console()],
});

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Always derive vault path from this file's location — never trust VAULT_PATH env var
// which may contain the placeholder value from .env.example.
const VAULT_PATH    = path.resolve(__dirname, '../..');
const APPROVED_DIR  = path.join(VAULT_PATH, 'Approved');
const DONE_DIR      = path.join(VAULT_PATH, 'Done');
const REJECTED_DIR  = path.join(VAULT_PATH, 'Rejected');

const LI_EMAIL     = process.env.LINKEDIN_EMAIL;
const LI_PASSWORD  = process.env.LINKEDIN_PASSWORD;
const HEADLESS     = process.env.HEADLESS !== 'false'; // default: true (headless)

// Session state file — avoids logging in every time
const SESSION_FILE = path.join(__dirname, '.linkedin_session.json');

// ---------------------------------------------------------------------------
// Markdown frontmatter parser
// ---------------------------------------------------------------------------

function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) return { meta: {}, body: content };

  const meta = {};
  for (const line of match[1].split('\n')) {
    const kv = line.match(/^(\w[\w_-]*):\s*"?(.+?)"?\s*$/);
    if (kv) meta[kv[1]] = kv[2].trim();
  }
  return { meta, body: match[2] };
}

/**
 * Extract the post text from the draft markdown.
 * Looks for content between "## Post Content" and the next heading or HR.
 */
function extractPostContent(markdownBody) {
  const match = markdownBody.match(/## Post Content\s*\n([\s\S]*?)(?:\n---|\n##|$)/);
  if (match) {
    return match[1]
      .replace(/^>.*$/gm, '')          // strip blockquotes (warning banners)
      .replace(/\*Draft.*\*\s*$/gm, '') // strip footer
      .trim();
  }
  // Fallback: return body with common markdown artifacts stripped
  return markdownBody
    .replace(/^[>#*].*$/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

// ---------------------------------------------------------------------------
// LinkedIn automation via Playwright
// ---------------------------------------------------------------------------

/**
 * Log into LinkedIn and save session state.
 * Returns the page object for further use.
 */
async function getLinkedInPage(browser) {
  let context;

  // Try to restore saved session
  if (fs.existsSync(SESSION_FILE)) {
    try {
      const savedState = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf8'));
      context = await browser.newContext({ storageState: savedState });
      log.info('Restored LinkedIn session from saved state');
    } catch {
      log.warn('Saved session invalid — will log in fresh');
      context = await browser.newContext();
    }
  } else {
    context = await browser.newContext();
  }

  const page = await context.newPage();
  await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded' });

  // Check if already logged in
  const isLoggedIn = await page.locator('[data-test-id="share-button"], .share-box-feed-entry__trigger').count();
  if (isLoggedIn > 0) {
    log.info('Already logged into LinkedIn');
    return { browser, context, page };
  }

  // Login flow
  log.info('Logging into LinkedIn...');
  await page.goto('https://www.linkedin.com/login', { waitUntil: 'domcontentloaded' });
  await page.fill('#username', LI_EMAIL);
  await page.fill('#password', LI_PASSWORD);
  await page.click('[data-litms-control-urn="login-submit"], [type="submit"]');
  await page.waitForURL(/linkedin\.com\/feed/, { timeout: 30_000 });

  log.info('Login successful');

  // Save session state for future runs
  const state = await context.storageState();
  fs.writeFileSync(SESSION_FILE, JSON.stringify(state), 'utf8');
  log.info('Session state saved');

  return { browser, context, page };
}

/**
 * Create a LinkedIn text post with the given content.
 */
async function postToLinkedIn(postText) {
  const browser = await chromium.launch({ headless: HEADLESS });

  try {
    const { context, page } = await getLinkedInPage(browser);

    log.info('Navigating to LinkedIn feed to create post...');
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded' });

    // Open the "Start a post" modal
    const startPostBtn = page.locator('.share-box-feed-entry__trigger, [aria-label*="Start a post"]').first();
    await startPostBtn.waitFor({ timeout: 15_000 });
    await startPostBtn.click();

    // Wait for the post editor
    const editor = page.locator('.ql-editor, [contenteditable="true"][role="textbox"]').first();
    await editor.waitFor({ timeout: 10_000 });
    await editor.click();
    await editor.fill(postText);

    log.info(`Post text entered (${postText.length} chars)`);

    // Click Post button
    const postBtn = page.locator(
      'button[aria-label="Post"], .share-actions__primary-action'
    ).first();
    await postBtn.waitFor({ timeout: 10_000 });
    await postBtn.click();

    // Wait for confirmation
    await page.waitForTimeout(3_000);

    // Save updated session
    const state = await context.storageState();
    fs.writeFileSync(SESSION_FILE, JSON.stringify(state), 'utf8');

    log.info('Post submitted successfully');
    return { success: true };

  } catch (err) {
    log.error(`LinkedIn post failed: ${err.message}`);
    return { success: false, error: err.message };
  } finally {
    await browser.close();
  }
}

// ---------------------------------------------------------------------------
// Process one approved file
// ---------------------------------------------------------------------------

async function processApprovedFile(filePath) {
  const filename = path.basename(filePath);
  const content  = fs.readFileSync(filePath, 'utf8');
  const { meta, body } = parseFrontmatter(content);

  if (meta.type !== 'linkedin_draft') {
    log.info(`Skipping ${filename} — type is '${meta.type}', not 'linkedin_draft'`);
    return;
  }

  if (meta.send_via_mcp !== 'linkedin-mcp') {
    log.info(`Skipping ${filename} — send_via_mcp is '${meta.send_via_mcp}'`);
    return;
  }

  log.info(`Processing approved LinkedIn draft: ${filename}`);
  log.info(`  Topic: ${meta.topic}  Type: ${meta.post_type}`);

  const postText = extractPostContent(body);

  if (!postText || postText.length < 10) {
    log.error(`Cannot extract post content from ${filename} — aborting`);
    return;
  }

  log.info(`  Post preview: "${postText.substring(0, 80)}..."`);

  const result = await postToLinkedIn(postText);

  const timestamp = new Date().toISOString();

  if (result.success) {
    // Mark as posted and move to Done/
    const updatedContent = content
      .replace('status: pending', 'status: posted')
      .replace('approved: false', 'approved: true')
      + `\n\n---\n\n**Posted by linkedin-mcp:** ${timestamp}\n`;

    const donePath = path.join(DONE_DIR, filename);
    fs.writeFileSync(donePath, updatedContent, 'utf8');
    fs.unlinkSync(filePath);

    log.info(`Moved to Done/: ${filename}`);
  } else {
    // Write error note and move to Rejected/
    const errorContent = content
      + `\n\n---\n\n**Post FAILED:** ${timestamp}\n**Error:** ${result.error}\n`;

    const rejectedPath = path.join(REJECTED_DIR, filename);
    fs.writeFileSync(rejectedPath, errorContent, 'utf8');
    fs.unlinkSync(filePath);

    log.warn(`Moved to Rejected/ due to post failure: ${filename}`);
  }
}

// ---------------------------------------------------------------------------
// Folder watcher
// ---------------------------------------------------------------------------

function ensureDirs() {
  for (const dir of [APPROVED_DIR, DONE_DIR, REJECTED_DIR]) {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  }
}

function startWatcher() {
  ensureDirs();

  const watcher = chokidar.watch(path.join(APPROVED_DIR, '*.md'), {
    persistent: true,
    ignoreInitial: false,
    awaitWriteFinish: { stabilityThreshold: 500, pollInterval: 100 },
  });

  watcher.on('add', async (filePath) => {
    log.info(`New file detected in Approved/: ${path.basename(filePath)}`);
    try {
      await processApprovedFile(filePath);
    } catch (err) {
      log.error(`Unexpected error: ${err.message}`, { stack: err.stack });
    }
  });

  watcher.on('error', (err) => log.error(`Watcher error: ${err.message}`));

  log.info(`Watching for approved LinkedIn drafts in: ${APPROVED_DIR}`);
}

// ---------------------------------------------------------------------------
// Startup validation
// ---------------------------------------------------------------------------

function validateConfig() {
  const missing = [];
  if (!LI_EMAIL)    missing.push('LINKEDIN_EMAIL');
  if (!LI_PASSWORD) missing.push('LINKEDIN_PASSWORD');

  if (missing.length > 0) {
    log.error(`Missing required environment variables: ${missing.join(', ')}`);
    log.error('Copy .env.example to .env and fill in your LinkedIn credentials.');
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

log.info('AI Employee LinkedIn MCP Server — Silver Tier');
log.info(`Vault: ${VAULT_PATH}`);
log.info(`Headless mode: ${HEADLESS}`);

validateConfig();
startWatcher();
