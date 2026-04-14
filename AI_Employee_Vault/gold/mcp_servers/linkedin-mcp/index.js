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

const LI_EMAIL     = process.env.LINKEDIN_EMAIL    || 'demo@example.com';
const LI_PASSWORD  = process.env.LINKEDIN_PASSWORD || 'demo';
const HEADLESS     = process.env.HEADLESS !== 'false'; // default: true (headless)

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
// LinkedIn automation via Playwright (persistent context)
// ---------------------------------------------------------------------------

// Persistent browser profile directory — accumulates cookies/history between runs
// so LinkedIn treats this as a real returning user, not a bot.
const PROFILE_DIR = path.join(__dirname, '.browser_profile');

/**
 * Create a LinkedIn text post with the given content.
 * Uses launchPersistentContext so the browser profile is saved between runs —
 * LinkedIn sees a familiar returning browser and skips security challenges.
 */
async function postToLinkedIn(postText) {
  const context = await chromium.launchPersistentContext(PROFILE_DIR, {
    headless: HEADLESS,
    args: [
      '--disable-blink-features=AutomationControlled',
      '--no-sandbox',
      '--disable-setuid-sandbox',
    ],
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 720 },
    locale: 'en-GB',
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });

  try {
    const page = await context.newPage();

    // Check if already logged in
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 30_000 });

    if (!page.url().includes('linkedin.com/feed')) {
      // Not logged in — perform fresh login
      log.info('Logging into LinkedIn...');
      await page.goto('https://www.linkedin.com/login', { waitUntil: 'domcontentloaded', timeout: 30_000 });
      await page.waitForSelector('#username', { timeout: 60_000 });
      await page.fill('#username', LI_EMAIL);
      await page.fill('#password', LI_PASSWORD);
      await page.click('[data-litms-control-urn="login-submit"], [type="submit"]');
      await page.waitForURL(/linkedin\.com\/feed/, { timeout: 60_000 });
      log.info('Login successful — profile saved to .browser_profile/');
    } else {
      log.info('Already logged into LinkedIn (persistent profile)');
    }

    log.info('Navigating to LinkedIn feed to create post...');
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded', timeout: 30_000 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(2_000);

    // Open the "Start a post" modal
    const startPostBtn = page.locator('[aria-label="Start a post"], .share-box-feed-entry__trigger, [aria-label*="Start a post"]').first();
    await startPostBtn.waitFor({ state: 'visible', timeout: 20_000 });
    await startPostBtn.click({ force: true });
    log.info('Clicked Start a post button');

    // Wait for modal animation to fully complete before looking for editor
    await page.waitForTimeout(4_000);

    // Wait for LinkedIn's post editor — covers Quill editor, modal contenteditable, and share creation state
    // Use state:visible so we only interact with a rendered, clickable editor
    log.info('Looking for post editor...');
    const editor = page.locator(
      'div.ql-editor[contenteditable="true"], ' +
      '.share-creation-state div[contenteditable="true"], ' +
      '.artdeco-modal div[contenteditable="true"]'
    ).first();
    await editor.waitFor({ state: 'visible', timeout: 45_000 });
    await editor.click({ force: true });
    await page.waitForTimeout(500);
    await page.keyboard.type(postText, { delay: 30 });

    log.info(`Post text entered (${postText.length} chars)`);

    // Click Post button
    const postBtn = page.locator(
      'button.share-actions__primary-action, button[aria-label="Post"], .artdeco-button--primary[aria-label="Post"]'
    ).first();
    await postBtn.waitFor({ state: 'visible', timeout: 20_000 });
    await postBtn.click({ force: true });

    // Wait for post to be submitted
    await page.waitForTimeout(5_000);

    log.info('Post submitted successfully');
    return { success: true };

  } catch (err) {
    log.error(`LinkedIn post failed: ${err.message}`);
    return { success: false, error: err.message };
  } finally {
    await context.close();
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
  if (!LI_EMAIL || LI_EMAIL === 'demo@example.com')    missing.push('LINKEDIN_EMAIL');
  if (!LI_PASSWORD || LI_PASSWORD === 'demo') missing.push('LINKEDIN_PASSWORD');

  if (missing.length > 0) {
    log.error(`Missing required environment variables: ${missing.join(', ')}`);
    log.error('Copy .env.example to .env and fill in your LinkedIn credentials.');
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

log.info('AI Employee LinkedIn MCP Server — Gold Tier [LIVE]');
log.info(`Vault: ${VAULT_PATH}`);
log.info(`Headless mode: ${HEADLESS}`);

validateConfig();
startWatcher();
