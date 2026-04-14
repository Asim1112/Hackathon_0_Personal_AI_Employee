---
type: demo_guide
tier: gold
created: 2026-04-10T00:00:00Z
created_by: claude_code
version: 1.0
audience: demo_presenter
---

# Demo Video Recording Guide — Gold Tier Personal AI Employee

> **Who this guide is for:** You — Asim — recording the Gold Tier demo video.
> **How to use it:** Work through Parts A → B in order before you press Record. Keep Part F (Quick Reference Card) open on a second monitor or printed out during recording.
> **Prerequisite:** All 5 MCP servers are now fully live with zero DRY_RUN mode. Every action you demo will hit the real APIs.

---

## Table of Contents

- [Part A — Pre-Recording Setup Checklist](#part-a--pre-recording-setup-checklist)
  - [A1 — Credentials & Accounts](#a1--credentials--accounts)
  - [A2 — Software & Tools](#a2--software--tools)
  - [A3 — Screen Layout Setup](#a3--screen-layout-setup)
  - [A4 — Vault State Verification](#a4--vault-state-verification)
- [Part B — Opening 6 Terminal Tabs](#part-b--opening-6-terminal-tabs)
- [Part C — The Demo Recording Script](#part-c--the-demo-recording-script)
  - [Scene 1 — The Vault Nerve Centre](#scene-1--opening-shot-the-vault-nerve-centre)
  - [Scene 2 — The Incoming Queue](#scene-2--show-the-incoming-queue)
  - [Scene 3 — MCP Servers Running](#scene-3--show-the-mcp-servers-running)
  - [Scene 4 — Trigger the Orchestrator](#scene-4--trigger-the-orchestrator)
  - [Scene 5 — The HITL Moment](#scene-5--the-hitl-moment-human-in-the-loop-approval)
  - [Scene 6 — The Live Result](#scene-6--show-the-live-result)
  - [Scene 7 — Remaining Approvals](#scene-7--repeat-hitl-for-remaining-items)
  - [Scene 8 — The Audit Log](#scene-8--the-audit-log)
  - [Scene 9 — The CEO Briefing](#scene-9--the-ceo-briefing-bonus-wow-moment)
  - [Scene 10 — Architecture Close](#scene-10--the-architecture-close)
- [Part D — Between-Takes Reset Procedure](#part-d--between-takes-reset-procedure)
- [Part E — Troubleshooting](#part-e--troubleshooting)
- [Part F — Quick Reference Card](#part-f--quick-reference-card)

---

# Part A — Pre-Recording Setup Checklist

> Complete every item in this section before you open OBS or press Record. Skipping any item risks a live failure mid-take.

---

## A1 — Credentials & Accounts

This section tells you exactly what credentials are needed, where to find them, and which `.env` fields to fill in. **The `.env` file is at the vault root:** `F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\gold\.env`

---

### ✅ Twitter/X — 5 API Keys Required

Twitter uses **OAuth 1.0a** — you need keys for both your App and your specific user account. All 5 are required; the MCP server exits immediately if any are missing.

| .env Field | What It Is | Where to Find It |
|---|---|---|
| `TWITTER_API_KEY` | Your App's Consumer Key | Twitter Developer Portal → Project → App → Keys and Tokens → Consumer Keys |
| `TWITTER_API_SECRET` | Your App's Consumer Secret | Same page as above |
| `TWITTER_ACCESS_TOKEN` | Your account's Access Token | Same page → Authentication Tokens → Access Token and Secret |
| `TWITTER_ACCESS_TOKEN_SECRET` | Your account's Access Token Secret | Same page as above |
| `TWITTER_BEARER_TOKEN` | App-level read token (used by the watcher) | Same page → Bearer Token |

**How to get them (step by step):**
1. Go to [developer.twitter.com](https://developer.twitter.com) and sign in with the account that will be posting
2. Open your Project → App → **Keys and Tokens** tab
3. If you haven't generated Access Token/Secret yet, click **Generate** under Authentication Tokens
4. Copy all 5 values into `.env`

⚠️ **Access Token type matters.** The Access Token must be generated with **Read and Write** permission. If you only have Read permission, the tweet post will fail with a 403 error. To change: Developer Portal → App → Settings → User authentication settings → App permissions → set to "Read and Write".

---

### ✅ Facebook — 2 Credentials Required

Facebook posting uses the **Meta Graph API v19.0**. You post to a Facebook Page (not a personal profile), so you need the Page's ID and an access token that has permission to manage it.

| .env Field | What It Is | Where to Find It |
|---|---|---|
| `FACEBOOK_PAGE_ID` | The numeric ID of your Facebook Page | See instructions below |
| `FACEBOOK_ACCESS_TOKEN` | A Page Access Token with `pages_manage_posts` permission | See instructions below |

**Finding your Page ID:**
1. Go to your Facebook Page
2. Click **About** → scroll down to find "Page ID" (a long number like `990237767514098`)
3. Or: go to `facebook.com/your-page-name/about` and look in the URL or page info

**Getting a Page Access Token (long-lived, recommended for demo):**
1. Go to [Meta for Developers](https://developers.facebook.com) → **Tools** → **Graph API Explorer**
2. In the top-right dropdown, select your App
3. Click **Generate Access Token** → grant all pages permissions when prompted
4. In the left panel, change the token type to **Page Access Token** and select your Page
5. The token shown is a **short-lived token** (1 hour). To make it long-lived (60 days):
   - Use the **Access Token Debugger** at [developers.facebook.com/tools/debug/accesstoken](https://developers.facebook.com/tools/debug/accesstoken)
   - Or call: `GET /oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN`
6. Copy the resulting token into `FACEBOOK_ACCESS_TOKEN` in `.env`

⚠️ **For a demo, a short-lived token is fine** — just generate it 30 minutes before recording. Long-lived tokens are better for production.

---

### ✅ Instagram — 1 Credential Required

Instagram posting requires a **Business or Creator account** (not a personal account). The account must be linked to your Facebook Page.

| .env Field | What It Is | Where to Find It |
|---|---|---|
| `INSTAGRAM_ACCOUNT_ID` | The numeric ID of your Instagram Business account | See instructions below |

**Finding your Instagram Account ID:**
1. In Graph API Explorer, with your Page Access Token active, call:
   `GET /{your-page-id}?fields=instagram_business_account`
2. The response will contain `"instagram_business_account": {"id": "17841453644961036"}` — that number is your `INSTAGRAM_ACCOUNT_ID`

⚠️ **Linking requirement:** If you get a blank response, your Instagram account is not linked to the Facebook Page. Fix this in Facebook Business Suite → Settings → Instagram → Connect Account.

⚠️ **Instagram posts require an `image_url`.** The demo Facebook post does not need an image, but any Instagram post file must include a publicly accessible image URL. For the demo, the Odoo and Twitter items are better HITL demonstrations than Instagram.

---

### ✅ LinkedIn — 2 Credentials Required

LinkedIn is automated via **Playwright browser automation** — the MCP server literally opens a Chromium browser, logs into LinkedIn with your real credentials, and clicks the post button. There is no LinkedIn API key needed.

| .env Field | What It Is | Where to Find It |
|---|---|---|
| `LINKEDIN_EMAIL` | The email address you use to log into LinkedIn | Your LinkedIn login |
| `LINKEDIN_PASSWORD` | Your LinkedIn password | Your LinkedIn login |
| `HEADLESS` | Whether the browser is hidden (`true`) or visible (`false`) | Set in `.env` |

**For the demo:** Set `HEADLESS=false` in `.env` so the browser window is visible on camera. This makes the automation dramatically more impressive to watch.

⚠️ **LinkedIn 2FA:** If your account has two-factor authentication enabled, the browser will stop at the 2FA screen and wait. You will need to complete it manually (enter SMS code). To avoid this during recording, either disable 2FA temporarily or run the MCP server once before recording to save the session file (`.linkedin_session.json` in the `linkedin-mcp/` folder), then the MCP will reuse the saved session and skip login.

⚠️ **Playwright browser install:** Before the first run, install the Chromium browser:
```bash
cd mcp_servers/linkedin-mcp
npx playwright install chromium
```

---

### ✅ Odoo — Docker + Accounting Module

Odoo is a self-hosted ERP system running in Docker on your local machine.

| .env Field | What It Is | Expected Value |
|---|---|---|
| `ODOO_URL` | The address of your Odoo instance | `http://localhost:8069` |
| `ODOO_DB` | The database name | `ai_employee` |
| `ODOO_USERNAME` | Admin account email | Your Odoo admin email |
| `ODOO_PASSWORD` | Admin account password | Your Odoo admin password |

**Before recording, verify:**
1. **Docker Desktop is running** — check the system tray icon
2. **Odoo container is up** — open [http://localhost:8069](http://localhost:8069) in a browser. You should see the Odoo login screen or dashboard.
3. **Accounting module is installed** — log into Odoo, click the main menu (grid icon top-left), look for **Accounting** or **Invoicing** in the app list. If it's not there, go to Apps → search "Accounting" → Install. **The MCP server will fail to create invoices without this module.**
4. **Log in and verify** — after installing Accounting, navigate to Accounting → Customers → Invoices. The page should load without errors.

---

### ✅ SMTP / Email — Gmail App Password

The email MCP sends real emails via Gmail SMTP. Do **not** use your Gmail account password — use an **App Password** instead (Google requires this when 2FA is enabled).

| .env Field | What It Is | Expected Value |
|---|---|---|
| `SMTP_HOST` | The SMTP server address | `smtp.gmail.com` |
| `SMTP_PORT` | The SMTP port number | `587` |
| `SMTP_SECURE` | Whether to use TLS | `false` (587 uses STARTTLS) |
| `SMTP_USER` | Your Gmail address | `your@gmail.com` |
| `SMTP_PASS` | Your Gmail App Password | 16-character App Password |
| `SMTP_FROM` | The "From" display name + address | `"Your Name <your@gmail.com>"` |

**Generating a Gmail App Password:**
1. Go to your Google Account → Security → 2-Step Verification (must be enabled first)
2. Scroll down to **App passwords** → click it
3. Select **Mail** as the app, **Windows Computer** as the device
4. Click **Generate** — copy the 16-character password (no spaces)
5. Paste it into `SMTP_PASS` in `.env`

---

## A2 — Software & Tools

Everything in this section must be installed and verified **before** you start recording.

- [ ] **Node.js v18+**
  Run `node --version`. Expected output: `v18.x.x` or higher (v20+ recommended).
  If missing: download from [nodejs.org](https://nodejs.org) — install the LTS version.

- [ ] **npm dependencies installed for each MCP server**
  Each MCP server has its own `node_modules`. Run once for each:
  ```bash
  cd mcp_servers/email-mcp && npm install
  cd mcp_servers/twitter-mcp && npm install
  cd mcp_servers/odoo-mcp && npm install
  cd mcp_servers/facebook-instagram-mcp && npm install
  cd mcp_servers/linkedin-mcp && npm install && npx playwright install chromium
  ```
  ✅ You only need to do this once — not before every take.

- [ ] **Python 3.11+**
  Run `python --version`. Expected: `Python 3.11.x` or higher.

- [ ] **uv (Python package manager)**
  Run `uv --version`. Expected: `uv 0.x.x`.
  If missing: `pip install uv` or follow [docs.astral.sh/uv](https://docs.astral.sh/uv).
  Then install Python dependencies: `uv sync` from the vault root.

- [ ] **Claude Code CLI**
  Run `claude --version`. Expected: version 2.x or higher.
  If missing: `npm install -g @anthropic/claude-code`

- [ ] **Docker Desktop — running**
  Check system tray. The Docker whale icon should be animated/green, not stopped.
  Open [http://localhost:8069](http://localhost:8069) — you should see Odoo.
  If Odoo is not running: open Docker Desktop → find the `odoo` container stack → Start.

- [ ] **Obsidian**
  Must be pointing at the gold vault folder: `F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\gold`
  Open it now and confirm you can see Dashboard.md in the file explorer.

- [ ] **OBS Studio (Screen Recording)**
  OBS is recommended because:
  - It captures multiple sources simultaneously (terminal + Obsidian window)
  - It's free and adds no watermark
  - It supports 1080p60 recording with low CPU usage
  - You can set up scenes to switch between full-screen views
  Download from [obsproject.com](https://obsproject.com) if not installed.
  **Settings to configure before recording:**
  - Output → Recording Path: set to your desktop or a fast drive
  - Video → Base Resolution: 1920×1080
  - Video → Output Resolution: 1920×1080
  - Video → FPS: 30 (sufficient for terminal work)
  - Audio → Desktop audio: enabled (capture terminal sounds + any notifications)

- [ ] **Windows Terminal (Recommended)**
  Windows Terminal supports multiple tabs and split panes in one window, making it easy to show all MCP servers at once.
  Install from the Microsoft Store if not already installed.
  **Font size:** Open Settings → Profiles → Defaults → Appearance → Font size → set to **18** minimum. Text below 18pt is unreadable on a 1080p recording when played back.

---

## A3 — Screen Layout Setup

A clean, professional screen layout makes the demo look polished and is easier to follow. Here is the recommended setup for 1920×1080.

### Recommended Dual-Window Layout

```
┌─────────────────────────────┬─────────────────────────────────┐
│                             │                                 │
│   OBSIDIAN — Reading View   │   WINDOWS TERMINAL              │
│   Dashboard.md              │                                 │
│   (or current vault file)   │   [Tab 1] Email MCP             │
│                             │   [Tab 2] Twitter MCP           │
│   Width: ~45% of screen     │   [Tab 3] Odoo MCP              │
│                             │   [Tab 4] Facebook/IG MCP       │
│                             │   [Tab 5] LinkedIn MCP          │
│                             │   [Tab 6] Orchestrator          │
│                             │                                 │
│                             │   Width: ~55% of screen         │
└─────────────────────────────┴─────────────────────────────────┘
```

### Step-by-Step Layout Setup

1. **Open Obsidian** and drag it to the left half of the screen. Resize to ~45% width.
   - In Obsidian, press `Ctrl+Shift+E` to toggle the Reading View (rendered Markdown).
   - Open Dashboard.md from the left sidebar.
   - In Reading View, the tables and formatting display cleanly — much better on camera than Edit View.

2. **Open Windows Terminal** and drag it to fill the right 55% of the screen.

3. **Create 6 tabs** in Windows Terminal:
   - Press `Ctrl+Shift+T` to open a new tab (repeat 6 times).
   - Right-click each tab → Rename: "Email MCP", "Twitter MCP", "Odoo MCP", "FB/IG MCP", "LinkedIn MCP", "Orchestrator"
   - Navigate each tab to the vault root:
     ```bash
     cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\gold"
     ```

4. **Obsidian font size:** `Ctrl+Shift+,` → open Settings → Editor → Font size → set to 16 minimum. Or use `Ctrl+=` to zoom in.

5. **Before pressing Record:** verify the layout fills the screen completely with no desktop visible behind either window.

---

## A4 — Vault State Verification

Before every take (first recording and every reset), verify the vault is in a clean, staged state. This ensures the demo runs exactly as planned.

### Step 1 — Run the Reset

This command resets the vault to a perfect demo-ready state. Run it from the vault root:

```bash
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\gold"
uv run python reset_demo.py
```

**What this does:**
- Creates any missing folders (`Pending_Approval/`, `Approved/`, etc.)
- Clears `Needs_Action/`, `Inbox/`, `Pending_Approval/`, `Approved/` — moves any stale files to `Archive/`
- Writes 5 fresh demo source files to `Needs_Action/` (dated today)
- Resets `Dashboard.md` to show "5 items pending, queue loaded"
- Does **NOT** touch `Done/`, `Logs/`, or `Briefings/`

### Step 2 — Generate the CEO Briefing (first time only)

The `Briefings/` folder must contain a `CEO_BRIEFING_<date>.md` file for Scene 9. If it is empty, generate it now:

```bash
uv run python orchestrator.py --briefing
```

This takes 2–3 minutes. Claude will generate the full weekly briefing and save it to `Briefings/`. You only need to do this once — the briefing file survives resets.

### Step 3 — Run the State Check

The reset script prints a full state check at the end. You can also run a standalone check at any time:

```bash
uv run python -c "
from pathlib import Path
v = Path('.')
checks = [
  ('Needs_Action has 5 files',    lambda: len(list((v/'Needs_Action').glob('*.md'))) == 5),
  ('Inbox is empty',              lambda: len(list((v/'Inbox').glob('*.md'))) == 0),
  ('Pending_Approval is empty',   lambda: len(list((v/'Pending_Approval').glob('*.md'))) == 0),
  ('Approved is empty',           lambda: len(list((v/'Approved').glob('*.md'))) == 0),
  ('Done has history',            lambda: len(list((v/'Done').glob('*.md'))) > 0),
  ('Logs has audit files',        lambda: len(list((v/'Logs').glob('*.json'))) > 0),
  ('Briefings has CEO briefing',  lambda: len(list((v/'Briefings').glob('*.md'))) > 0),
  ('Dashboard.md exists',         lambda: (v/'Dashboard.md').exists()),
  ('CLAUDE.md exists',            lambda: (v/'CLAUDE.md').exists()),
]
all_ok = True
for name, fn in checks:
    r = fn()
    print('[OK]' if r else '[!!]', name)
    if not r: all_ok = False
print()
print('READY TO RECORD' if all_ok else 'NOT READY — fix issues above')
"
```

### ✅ What a Perfect GO Output Looks Like

```
[OK] Needs_Action has 5 files
[OK] Inbox is empty
[OK] Pending_Approval is empty
[OK] Approved is empty
[OK] Done has history
[OK] Logs has audit files
[OK] Briefings has CEO briefing
[OK] Dashboard.md exists
[OK] CLAUDE.md exists

READY TO RECORD
```

### ❌ What a NOT READY Output Looks Like (and Fixes)

```
[!!] Needs_Action has 5 files     → Fix: uv run python reset_demo.py
[!!] Pending_Approval is empty    → Fix: uv run python reset_demo.py
[!!] Briefings has CEO briefing   → Fix: uv run python orchestrator.py --briefing
[OK] Done has history
[OK] Logs has audit files
...

NOT READY — fix issues above
```

Run the indicated command for each `[!!]` line, then re-run the check until all lines show `[OK]`.

---

# Part B — Opening 6 Terminal Tabs

Open all 6 tabs **before** pressing Record. MCP servers need to be running and showing their "watching" message before you trigger the orchestrator on camera.

All commands below should be run from the vault root. If you renamed your tabs as suggested in A3, navigate each tab there first:

```bash
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\gold"
```

---

## Tab 1 — Email MCP

```bash
node mcp_servers/email-mcp/index.js
```

**What this does:** This server watches the `Approved/` folder for email draft files. When you move a `DRAFT_REPLY_*.md` file from `Inbox/` to `Approved/`, this server picks it up, reads the recipient address and subject from the file's frontmatter, and sends the email via Gmail SMTP using your `SMTP_*` credentials. It then moves the file to `Done/` with a timestamp and message ID.

**Successful startup looks like:**
```
2026-04-10T09:00:00+00:00 [email-mcp] INFO  Silver AI Employee · Email MCP Server [LIVE]
2026-04-10T09:00:00+00:00 [email-mcp] INFO  Vault : F:\...\gold
2026-04-10T09:00:00+00:00 [email-mcp] INFO  SMTP  : smtp.gmail.com:587 (user: your@gmail.com)
2026-04-10T09:00:00+00:00 [email-mcp] INFO  Flow  : /Inbox (Claude drafts) → /Approved (human approves) → sent → /Done
2026-04-10T09:00:00+00:00 [email-mcp] INFO  Watching /Approved — waiting for approved email drafts…
```

**If startup fails:**
- `smtp_user / smtp_pass not set` → your `SMTP_USER` and `SMTP_PASS` are blank in `.env`. Fill them in.
- `Cannot find module 'nodemailer'` → run `npm install` in `mcp_servers/email-mcp/` first.

---

## Tab 2 — Twitter MCP

```bash
node mcp_servers/twitter-mcp/index.js
```

**What this does:** This server watches `Approved/` for files with `type: social_draft` and `send_via_mcp: twitter-mcp`. When triggered, it reads the tweet content from the file's JSON action block and posts it via the Twitter API v2. It supports single tweets and threads. After posting, it moves the file to `Done/` with the tweet ID.

**Successful startup looks like:**
```
2026-04-10T09:00:01+00:00 [twitter-mcp] INFO  Gold AI Employee · Twitter MCP Server [LIVE]
2026-04-10T09:00:01+00:00 [twitter-mcp] INFO  Vault: F:\...\gold
2026-04-10T09:00:01+00:00 [twitter-mcp] INFO  Flow: TWITTER_DRAFT_*.md → /Approved (human) → posted → /Done
2026-04-10T09:00:01+00:00 [twitter-mcp] INFO  Watching /Approved — waiting for approved tweet drafts…
```

**If startup fails:**
- `Missing Twitter credentials` → one or more `TWITTER_*` keys are blank in `.env`. Check all 4 OAuth keys are filled.
- `Cannot find module 'twitter-api-v2'` → run `npm install` in `mcp_servers/twitter-mcp/` first.

---

## Tab 3 — Odoo MCP

```bash
node mcp_servers/odoo-mcp/index.js
```

**What this does:** This server watches `Approved/` for files with `type: odoo_action` and `send_via_mcp: odoo-mcp`. When triggered, it connects to your local Odoo instance via JSON-RPC and executes the action specified (create invoice, confirm invoice, or sync accounting data). After success, it moves the file to `Done/` with a link to the new Odoo record.

**Successful startup looks like:**
```
2026-04-10T09:00:02+00:00 [odoo-mcp] INFO    Odoo reachable — server version: 17.0
2026-04-10T09:00:02+00:00 [odoo-mcp] INFO    Authenticated as uid: 2 (db: ai_employee)
2026-04-10T09:00:02+00:00 [odoo-mcp] INFO    ──────────────────────────────────────────────
2026-04-10T09:00:02+00:00 [odoo-mcp] INFO    Gold AI Employee · Odoo MCP Server [LIVE]
2026-04-10T09:00:02+00:00 [odoo-mcp] INFO    Vault   : F:\...\gold
2026-04-10T09:00:02+00:00 [odoo-mcp] INFO    Odoo    : http://localhost:8069 / db: ai_employee
2026-04-10T09:00:02+00:00 [odoo-mcp] INFO    Actions : create_invoice | confirm_invoice | sync_accounting
2026-04-10T09:00:02+00:00 [odoo-mcp] INFO    Watching /Approved — waiting for approved Odoo actions…
```

**If startup fails:**
- `Cannot connect to Odoo` → Docker container is not running. Start it in Docker Desktop.
- `Authentication failed` → wrong `ODOO_PASSWORD` in `.env`. Check the Odoo admin credentials.
- `Cannot find module './odoo-client'` → run `npm install` in `mcp_servers/odoo-mcp/` first.

---

## Tab 4 — Facebook/Instagram MCP

```bash
node mcp_servers/facebook-instagram-mcp/index.js
```

**What this does:** This server watches `Approved/` for files with `type: social_post` and `send_via_mcp: facebook-instagram-mcp`. For Facebook, it posts to your Page feed via the Meta Graph API v19.0. For Instagram, it creates a media container (with your image URL) and then publishes it — a two-step process required by Meta's API.

**Successful startup looks like:**
```
2026-04-10T09:00:03Z [fb-ig-mcp] INFO  Gold AI Employee · Facebook & Instagram MCP Server [LIVE]
2026-04-10T09:00:03Z [fb-ig-mcp] INFO  Vault     : F:\...\gold
2026-04-10T09:00:03Z [fb-ig-mcp] INFO  FB Page   : 990237767514098
2026-04-10T09:00:03Z [fb-ig-mcp] INFO  IG Account: 17841453644961036
2026-04-10T09:00:03Z [fb-ig-mcp] INFO  Watching /Approved — waiting for approved FB/IG post drafts…
```

**If startup fails:**
- `FACEBOOK_ACCESS_TOKEN not set` → fill in `FACEBOOK_ACCESS_TOKEN` in `.env`.
- `Cannot find module 'chokidar'` → run `npm install` in `mcp_servers/facebook-instagram-mcp/` first.

---

## Tab 5 — LinkedIn MCP

```bash
node mcp_servers/linkedin-mcp/index.js
```

**What this does:** This server watches `Approved/` for files with `type: linkedin_draft` and `send_via_mcp: linkedin-mcp`. When triggered, it launches a Chromium browser using Playwright, logs into LinkedIn (or restores a saved session), navigates to the feed, clicks "Start a post", types the post content, and clicks Post. Because LinkedIn has no public posting API for personal profiles, browser automation is the only reliable method.

**Successful startup looks like (with `HEADLESS=false`):**
```
2026-04-10T09:00:04+00:00 [linkedin-mcp] INFO    AI Employee LinkedIn MCP Server — Gold Tier [LIVE]
2026-04-10T09:00:04+00:00 [linkedin-mcp] INFO    Vault: F:\...\gold
2026-04-10T09:00:04+00:00 [linkedin-mcp] INFO    Headless mode: false
2026-04-10T09:00:04+00:00 [linkedin-mcp] INFO    Watching for approved LinkedIn drafts in: F:\...\gold\Approved
```

Then it sits idle, watching. When a file is approved, you will see Chromium browser open automatically.

**If startup fails:**
- `Missing required environment variables: LINKEDIN_EMAIL, LINKEDIN_PASSWORD` → fill both in `.env`.
- `browserType.launch: Executable doesn't exist` → run `npx playwright install chromium` in `mcp_servers/linkedin-mcp/`.
- LinkedIn 2FA pop-up when a file is processed → see Part E — Troubleshooting.

---

## Tab 6 — Orchestrator (Ready but not yet running)

**Do not run this tab yet.** Just have the command ready. You will run it on camera in Scene 4.

```bash
uv run python orchestrator.py --cron
```

Type this command into Tab 6 but **do not press Enter**. You will press Enter on camera during Scene 4 as the "trigger moment" of the demo.

**What this does when run:** The `--cron` flag runs one complete daily triage cycle and then exits. It calls `claude --dangerously-skip-permissions --print` with the full daily workflow prompt, which instructs Claude to run all 13 skills in sequence: Daily Briefing → Gmail Triage → WhatsApp Triage → LinkedIn Draft → Twitter Draft → Facebook/Instagram → Odoo Accounting → Reasoning Loop → Process Needs Action → Audit Logger → Update Dashboard. Claude processes all 5 queue items, writes output files, and exits with `TASK_COMPLETE`.

---

# Part C — The Demo Recording Script

> **How to use this script:** Read the SHOW/SAY/DO blocks for each scene before recording. The SAY blocks are written to be read aloud verbatim — they are natural, not robotic. Adapt them slightly if you prefer different phrasing.

---

## Scene 1 — Opening Shot: The Vault Nerve Centre

**Duration:** ~45 seconds

**SHOW:** Obsidian in Reading View, displaying `Dashboard.md`. The System Status table should be visible at the top with 5 items in the queue.

**DO:** Before recording this scene, scroll Dashboard.md to show the System Status table and the "Needs Action Queue" table in the same view if possible.

**SAY:**
> "This is the Gold Tier Personal AI Employee. What you're looking at is the Dashboard — the nerve centre of the system. Everything the AI has done, is doing, and needs to do is tracked here in real time.
>
> Right now, the queue has five items waiting: an email from an existing client with a board meeting deadline, a new LinkedIn contact who could be a high-value lead, a Twitter post request, a Facebook business page announcement, and — the most interesting one — an overdue invoice worth £2,400 that needs to be created in Odoo.
>
> None of these have been touched yet. The AI Employee is waiting for its next processing cycle to begin. Let me show you what's in the queue first."

---

## Scene 2 — Show the Incoming Queue

**Duration:** ~2 minutes

**SHOW:** Obsidian sidebar open, showing the `Needs_Action/` folder with 5 files.

**DO:** Click through each file in the sidebar to open it, hold for 5–10 seconds, then move to the next.

### File 1: EMAIL
Click `EMAIL_<date>_AI_Project_Milestone_demo01.md`

**SAY:**
> "The first item is an inbound email. Sarah Johnson from TechCorp Ltd — an existing client — is asking for a project status update before her board meeting on Friday. She has three specific questions about the AI integration project. This is a high-priority item because of the Friday deadline. The AI will draft a professional reply covering all three points."

### File 2: LINKEDIN
Click `LINKEDIN_<date>_enterprise_automation_enquiry_demo02.md`

**SAY:**
> "Item two is a LinkedIn opportunity. Marcus Webb, Chief Operating Officer at Apex Advisory Partners — a 45-person professional services firm — has sent a direct message expressing interest in AI automation. He's described three specific pain points that map exactly to our service offering. Notice the flag: `is_new_contact: true`. That means no reply can be sent until a human has approved it — the new contact rule kicks in automatically."

### File 3: TWITTER
Click `TWITTER_<date>_post_request_demo03.md`

**SAY:**
> "Item three is a Twitter post request. An internal content task asking the AI to draft a standalone tweet about the system's capabilities. The brief specifies maximum 280 characters, professional tone, and 2–3 hashtags. The AI will draft this and park it in Pending Approval — it never posts to social media without explicit human sign-off."

### File 4: FACEBOOK
Click `FACEBOOK_<date>_post_request_demo04.md`

**SAY:**
> "Item four is a Facebook Business Page post. Same pattern — internal request, specific brief, goes to Pending Approval before anything touches the real platform."

### File 5: ODOO (highlight this one)
Click `ODOO_<date>_overdue_invoice_INV-2026-010.md`

**SAY:**
> "And the fifth item — this is the one I want you to pay attention to. Meridian Consulting Group. Invoice INV-2026-010. Amount: two thousand four hundred pounds. Overdue by 31 days. The Odoo watcher detected this and wrote it into the queue automatically. The AI will draft an invoice creation action for Odoo and an overdue payment chase email — but both go to Pending Approval first, because the amount is well above the £50 financial threshold. No money moves, no invoice is created, until a human says yes."

---

## Scene 3 — Show the MCP Servers Running

**Duration:** ~45 seconds

**SHOW:** Switch to Windows Terminal. Click through each of the 5 MCP tabs one by one.

**DO:** Click Tab 1, pause 3 seconds, click Tab 2, pause 3 seconds, and so on through Tab 5.

**SAY:**
> "Before I trigger the AI cycle, let me show you what's running in the background. Five MCP servers — Machine Control Processes — each one connected to a real external platform and watching the Approved folder for work to do.
>
> Tab one — the email MCP — connected to Gmail SMTP, ready to fire the moment an email draft gets approved. Tab two — Twitter — connected to the live Twitter API. Tab three — Odoo — authenticated to the local Odoo ERP instance running in Docker. Tab four — Facebook and Instagram — connected to the Meta Graph API. Tab five — LinkedIn — Playwright browser automation, credentials loaded, ready to open a real browser and post.
>
> None of these will do anything until a human moves a file into the Approved folder. That's the guarantee."

---

## Scene 4 — Trigger the Orchestrator

**Duration:** ~3–4 minutes (Claude runs in real time)

**SHOW:** Switch to Tab 6 — the Orchestrator tab. The command `uv run python orchestrator.py --cron` should already be typed and waiting.

**DO:** Press Enter. Let the output scroll. Do not narrate over the output — let the viewer read it.

**SAY (before pressing Enter):**
> "This is the moment. I'm going to trigger the daily processing cycle. This command calls Claude Code with the full workflow prompt. Watch what happens."

*[Press Enter]*

**SAY (as output scrolls — speak slowly, leave pauses):**
> "Claude is now reading the vault — the Company Handbook, the Business Goals, the Dashboard. It's going to work through all five items in order, applying the right specialist skill to each one.
>
> You can see the skill routing happening in real time. Email item — SKILL_Gmail_Triage. LinkedIn opportunity — SKILL_LinkedIn_Draft. Twitter request — SKILL_Twitter_Draft. Facebook — SKILL_Facebook_Instagram. And the Odoo alert — SKILL_Odoo_Accounting.
>
> Claude isn't a generalist here — it's using purpose-built skills for each channel, each with its own rules, templates, and escalation logic from the Company Handbook."

**SAY (when Claude finishes, before TASK_COMPLETE appears):**
> "And when the queue is empty, the system writes its completion signal — TASK_COMPLETE — and exits. The orchestrator stops. Nothing keeps running. Clean, auditable, deterministic."

---

## Scene 5 — The HITL Moment (Human-in-the-Loop Approval)

**Duration:** ~90 seconds — **this is the single strongest visual in the demo**

**SHOW:** Switch to Obsidian. Navigate to the `Pending_Approval/` folder in the sidebar.

**DO:** Click to expand `Pending_Approval/` — show all the files Claude has generated. There should be 5+ files: a LinkedIn draft, Twitter draft, Facebook draft, Odoo invoice action, and a new contact review.

**SAY:**
> "Claude has processed all five items. But nothing has been sent to the outside world yet. Every external action is sitting right here in Pending Approval — waiting for a human decision. This folder is the mandatory approval gate. If I never open it, nothing ever happens."

**DO:** Click to open the Odoo invoice file. It should be named something like `ODOO_REVIEW_Invoice_Meridian_Consulting_<date>.md`. Scroll slowly through it.

**SAY:**
> "Let me open the Odoo invoice action. You can see exactly what Claude drafted: Meridian Consulting Group, £2,400, the line item, the action type — create invoice. And right here in the frontmatter: `status: pending`, `send_via_mcp: odoo-mcp`. The MCP server will read these exact values when the file arrives in Approved.
>
> This is the moment where the human decides. I've reviewed it. It looks correct. I'm going to approve it."

**DO:**
1. In your file manager (Windows Explorer) — or directly in Obsidian if you have the File Manager plugin — move the Odoo file from `Pending_Approval/` to `Approved/`.
   - The simplest method: open Windows Explorer alongside Obsidian, navigate to `gold\Pending_Approval\`, drag the Odoo file to `gold\Approved\`

**SAY (immediately after moving):**
> "Watch Tab 3."

**DO:** Switch immediately to the Terminal, Tab 3 — the Odoo MCP tab.

**SAY:**
> *[pause — let the MCP output appear on screen for 3–5 seconds before speaking]*
> "There it is. The MCP server detected the file the moment it landed in Approved. It's connecting to Odoo right now — authenticating, calling the JSON-RPC API, creating the invoice record in the live ERP system. And it's done. Invoice created. The file has been moved to Done with a timestamp and the Odoo record ID."

---

## Scene 6 — Show the Live Result

**Duration:** ~45 seconds

**SHOW:** Open a browser tab with Odoo — [http://localhost:8069](http://localhost:8069)

**DO:** Navigate to Accounting → Customers → Invoices. The newly created invoice for Meridian Consulting Group should appear at the top of the list.

**SAY:**
> "This is Odoo — the real ERP system, running locally in Docker. And here's the invoice. Meridian Consulting Group. £2,400. Created seconds ago — not in a test environment, not in a sandbox, not simulated. The AI Employee just created a real accounting record in a real ERP system.
>
> This is what live looks like."

---

## Scene 7 — Repeat HITL for Remaining Items

**Duration:** ~60 seconds

**SHOW:** Return to Obsidian → `Pending_Approval/` folder.

**DO:** Open the Twitter draft file briefly, show its content, then move it to `Approved/`. Switch to Tab 2 (Twitter MCP) and show the tweet being posted.

**SAY:**
> "Let me show you one more. The Twitter draft — here it is in Pending Approval. Claude drafted this tweet, counted the characters, added the right hashtags. I'm moving it to Approved now.
>
> *[pause for MCP output]*
>
> And there it is — posted to the real Twitter account, tweet ID logged, file moved to Done. Same pattern. Every channel. Every time.
>
> The LinkedIn approval would open a real Chromium browser, log into LinkedIn with Playwright, and post. The Facebook approval would call the Meta Graph API. The email approval would trigger Gmail SMTP. Same HITL gate — different platform, different MCP — but the approval workflow never changes."

---

## Scene 8 — The Audit Log

**Duration:** ~60 seconds

**SHOW:** In Obsidian, navigate to the `Logs/` folder. Open the most recent `.json` file.

**DO:** Scroll slowly through the file. Find the entry for the Odoo action and hover over it.

**SAY:**
> "Every single action this system takes is written to a structured JSON audit log. One file per day. Let me read you one entry in full."

Read this entry (or find a similar one in the actual log):
> "Timestamp: 2026-03-26 at 08:48 UTC. Action type: odoo draft created. Actor: claude code. Target: the Odoo review file. Skill used: SKILL_Odoo_Accounting. Approval status: pending. Result: escalated. Notes: overdue invoice INV-2026-010, Meridian Consulting Group, £2,400, 31 days overdue — create invoice action written to Pending Approval. Amount above the £50 threshold, HITL rule applied."

**SAY:**
> "Eight fields. Every action. Who did it, what skill was used, what the approval status was, and what happened. Nothing in this system goes unrecorded. If something went wrong two weeks ago and you needed to trace it — every step is here."

---

## Scene 9 — The CEO Briefing (Bonus Wow Moment)

**Duration:** ~60 seconds

**SHOW:** In Obsidian, navigate to `Briefings/` and open `CEO_BRIEFING_<date>.md`.

**DO:** Scroll slowly through the briefing document. Pause on each section for 3–4 seconds.

**SAY:**
> "And finally — every Sunday at eleven PM, the system generates this. The CEO Briefing.
>
> *[scroll through Revenue section]*
> Revenue this week versus the £2,500 weekly target. Outstanding invoices. Overdue items flagged with the number of days.
>
> *[scroll through Social Media section]*
> Social media activity across all five channels. Posts published this week, drafts waiting for approval.
>
> *[scroll through Recommended Actions section]*
> And at the bottom — proactive recommendations. Not just a report of what happened. Suggestions for what to do next. Chase this client. Review this subscription. Follow up on this lead before the window closes.
>
> A business owner receives this on Monday morning before they've had their first coffee. Revenue versus target. Overdue invoices. SLA breaches. Three specific actions to take. Zero effort from the human. That's the Gold Tier AI Employee."

---

## Scene 10 — The Architecture Close

**Duration:** ~45 seconds

**SHOW:** In Obsidian, navigate to and open `CLAUDE.md`. Scroll to the Folder Structure section near the bottom.

**DO:** Scroll slowly so the folder tree is visible on screen.

**SAY:**
> "Let me close with the architecture. Six watchers monitoring five channels simultaneously — Email, WhatsApp, LinkedIn, Twitter, Facebook, and Odoo ERP. Every incoming item lands in a structured Markdown file in the Needs Action queue.
>
> Claude Code acts as the reasoning layer — reading the queue, applying thirteen specialist skills, and routing each item to the right output. No external action is ever taken directly. Everything sensitive goes to Pending Approval first.
>
> When a human approves, one of five MCP servers fires — connected to a real platform, executing the real action, and writing the result to the audit log.
>
> Full JSON audit trail. Weekly CEO briefing. Human approval at every external action point. This is the Gold Tier Personal AI Employee."

---

# Part D — Between-Takes Reset Procedure

If a take goes wrong — MCP fires too early, wrong file approved, terminal output is hard to read — use this procedure to get back to a clean state in under 30 seconds.

### Step 1 — Stop All MCP Servers (10 seconds)

In Windows Terminal, click each MCP tab and press `Ctrl+C` to stop it. You do not need to close the tabs — just kill the process.

- Tab 1: `Ctrl+C`
- Tab 2: `Ctrl+C`
- Tab 3: `Ctrl+C`
- Tab 4: `Ctrl+C`
- Tab 5: `Ctrl+C`

### Step 2 — Reset the Vault (5 seconds)

In Tab 6, run:

```bash
uv run python reset_demo.py
```

This clears `Needs_Action/`, `Inbox/`, `Pending_Approval/`, and `Approved/`, archives any stale files, writes 5 fresh demo files, and resets Dashboard.md. It takes about 3 seconds.

### Step 3 — Restart All MCP Servers (10 seconds)

In each MCP tab, press the Up arrow key to recall the previous command, then press Enter:

- Tab 1: ↑ Enter → `node mcp_servers/email-mcp/index.js`
- Tab 2: ↑ Enter → `node mcp_servers/twitter-mcp/index.js`
- Tab 3: ↑ Enter → `node mcp_servers/odoo-mcp/index.js`
- Tab 4: ↑ Enter → `node mcp_servers/facebook-instagram-mcp/index.js`
- Tab 5: ↑ Enter → `node mcp_servers/linkedin-mcp/index.js`

### Step 4 — Verify State (5 seconds)

Watch for the `[OK]` output lines at the end of the reset script. If all green, you are ready. If not, re-run the reset.

### Step 5 — Reload Dashboard in Obsidian

In Obsidian, close and reopen `Dashboard.md` to refresh the Reading View display.

### Notes

- ⏱ **Total reset time: under 30 seconds** if you are fluent with the keyboard shortcuts.
- ✅ **CEO Briefing does NOT need to be regenerated** — the `Briefings/` folder is untouched by the reset. The briefing file you generated in A4 Step 2 survives every reset.
- ✅ **Done/ and Logs/ are untouched** — the reset only clears active queue folders.
- ⚠️ **If Odoo already has the invoice from a previous take:** You may want to delete the test invoice in Odoo (Accounting → Invoices → open → Action → Delete) before the next take, so the "invoice appears live" moment is fresh. Alternatively, use the Facebook or Twitter approval for the HITL moment — no cleanup needed for those.

---

# Part E — Troubleshooting

---

## MCP Server Fails to Start

**Symptom:** Terminal shows error immediately on startup, no "watching" message.

| Error | Cause | Fix |
|---|---|---|
| `Cannot find module 'xxx'` | npm dependencies not installed | `cd mcp_servers/<name>-mcp && npm install` |
| `Missing Twitter credentials` | One or more `TWITTER_*` env vars blank | Fill all 5 Twitter keys in `.env` |
| `smtp_user / smtp_pass not set` | `SMTP_USER` or `SMTP_PASS` blank | Fill SMTP credentials in `.env` |
| `Cannot connect to Odoo` | Docker container not running | Start Docker Desktop, start Odoo stack |
| `FACEBOOK_ACCESS_TOKEN not set` | Facebook token blank in `.env` | Fill `FACEBOOK_ACCESS_TOKEN` in `.env` |
| `Missing required environment variables: LINKEDIN_EMAIL` | LinkedIn credentials blank | Fill `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` in `.env` |
| Process exits instantly with no message | Node.js not installed or wrong version | `node --version` — must be 18+. Install from nodejs.org |

---

## Twitter Post Fails

**Symptom:** MCP picks up the approved file but the tweet is rejected.

| Error | Cause | Fix |
|---|---|---|
| `Graph API error: 403 Forbidden` | Access Token has Read-only permission | Regenerate Access Token with Read+Write permission in Twitter Developer Portal |
| `Rate limit exceeded` | Too many API calls | Wait 15 minutes. Twitter API v2 has rate limits per 15-minute window. |
| `Invalid or expired token` | Access Token expired | Regenerate both Access Token and Access Token Secret in the Developer Portal |
| `Tweet text too long` | Character count >280 | The MCP posts whatever is in the `content` field — if Claude miscounted, manually edit the draft file before approving |

---

## LinkedIn MCP Fails

**Symptom:** MCP picks up the file, opens Chromium, but fails to post.

| Error | Cause | Fix |
|---|---|---|
| `Executable doesn't exist` | Playwright Chromium not installed | `cd mcp_servers/linkedin-mcp && npx playwright install chromium` |
| Browser opens but stops at 2FA screen | LinkedIn 2FA is blocking automated login | Option 1: Complete the 2FA manually in the open browser — the session will be saved. Option 2: Pre-run the MCP server before the demo to save the session, so login is skipped during the demo itself. Option 3: Temporarily disable 2FA on the LinkedIn account. |
| `Login successful` but post fails | LinkedIn changed their page selectors | This is a known risk with browser automation — LinkedIn updates its UI periodically. Check if the post editor selector still matches. |
| `Error: page.goto: net::ERR_INTERNET_DISCONNECTED` | No internet connection | Check connection. LinkedIn automation requires internet access. |

---

## Facebook / Instagram Post Fails

**Symptom:** MCP picks up the file but the Graph API returns an error.

| Error | Cause | Fix |
|---|---|---|
| `Graph API error: (#190) Access token has expired` | The Page Access Token has expired | Generate a new token using Graph API Explorer (see A1 — Facebook section). Replace `FACEBOOK_ACCESS_TOKEN` in `.env` and restart the MCP. |
| `Graph API error: (#200) The user hasn't authorized the application` | Token missing `pages_manage_posts` permission | When generating the token in Graph API Explorer, ensure you check the `pages_manage_posts` permission. |
| `Graph API error: Instagram requires an image` | Instagram post file missing `image_url` | Instagram posts must include a valid, publicly accessible `image_url`. Facebook posts do not require an image. For the demo, use Facebook. |
| `HTTP 400` | Malformed request body | Check the JSON action block in the draft file — `"message"` field must exist and be a non-empty string. |

---

## Odoo Connection Fails

**Symptom:** Odoo MCP startup fails or invoice creation fails.

| Error | Cause | Fix |
|---|---|---|
| `Cannot connect to Odoo: ECONNREFUSED` | Docker container not running | Open Docker Desktop → start the Odoo stack. Wait 30–60 seconds for Odoo to boot. |
| `Authentication failed: Wrong login` | `ODOO_USERNAME` or `ODOO_PASSWORD` incorrect | Log into [http://localhost:8069](http://localhost:8069) manually with the same credentials to verify. Correct `.env` if needed. |
| `action data missing required field: partner_name` | The JSON action block in the approved file is malformed | Open the file in Pending_Approval/, check the ` ```json ``` ` block has a `partner_name` field and a `lines` array. |
| `odoo.exceptions.UserError: The Accounting module is not installed` | Accounting/Invoicing module not enabled | Log into Odoo → Apps menu → search "Accounting" → Install. Wait for install to complete. |
| Invoice created but no line items | `lines` array in JSON is empty or malformed | Check the `lines` array in the action JSON: must have objects with `name`, `quantity`, and `price_unit` fields. |

---

## Orchestrator Stops Mid-Run

**Symptom:** The `--cron` command exits before printing `TASK_COMPLETE`.

**Most likely cause:** Claude Code timed out (the default timeout is 15 minutes) or hit a processing error.

**How to diagnose:**
1. Check the last few lines of the terminal output — they will say which skill was running when it stopped.
2. Check `Logs/<today>.json` — find the last logged entry to see how far Claude got.
3. Check `Needs_Action/` — any files still there did not get processed.

**Fix:**
1. Run the reset: `uv run python reset_demo.py`
2. Re-trigger: `uv run python orchestrator.py --cron`
3. If it keeps timing out, check that your machine is not under heavy load. Close other applications.

---

## Files Not Moving Between Folders

**Symptom:** You approved a file (moved it to `Approved/`) but the MCP server did nothing.

**Possible causes:**

1. **MCP server is not running.** Check the relevant terminal tab — the process may have crashed silently. Restart it.

2. **Wrong folder.** Files must go directly into `Approved/` — not into a subfolder like `Approved/email/`. The MCP watches `Approved/*.md` only.

3. **Wrong frontmatter.** The MCP uses exact string matching on `type:` and `send_via_mcp:` fields. If these don't match exactly, the file is silently skipped. Open the file and verify the frontmatter matches the MCP cheat sheet in `CLAUDE.md`.

4. **File encoding issue (Windows).** If you created or edited the file with PowerShell using `-Encoding utf8`, it may have added a BOM (Byte Order Mark) that breaks the YAML parser. The `type` field would appear as `type=?` in debug output. Use Python or VS Code (set to LF, no BOM) to create files.

5. **chokidar polling.** The MCP uses a 400–500ms write stabilisation delay. Very fast file operations may occasionally be missed. Wait 2 seconds after moving a file — if nothing happens after 5 seconds, the MCP likely skipped it due to a frontmatter mismatch.

---

# Part F — Quick Reference Card

> Print this page or keep it open on a second monitor during recording.

---

## 5 MCP Start Commands

```bash
node mcp_servers/email-mcp/index.js
node mcp_servers/twitter-mcp/index.js
node mcp_servers/odoo-mcp/index.js
node mcp_servers/facebook-instagram-mcp/index.js
node mcp_servers/linkedin-mcp/index.js
```

---

## Key Commands

```bash
uv run python reset_demo.py                  # Reset vault between takes
uv run python orchestrator.py --cron         # Trigger daily Claude cycle (demo)
uv run python orchestrator.py --briefing     # Generate CEO Briefing (one-off)
uv run python orchestrator.py                # Daemon mode (continuous + scheduled)
```

---

## State Check Command

```bash
uv run python -c "
from pathlib import Path
v = Path('.')
checks = [
  ('Needs_Action has 5 files',    lambda: len(list((v/'Needs_Action').glob('*.md'))) == 5),
  ('Inbox is empty',              lambda: len(list((v/'Inbox').glob('*.md'))) == 0),
  ('Pending_Approval is empty',   lambda: len(list((v/'Pending_Approval').glob('*.md'))) == 0),
  ('Approved is empty',           lambda: len(list((v/'Approved').glob('*.md'))) == 0),
  ('Briefings has CEO briefing',  lambda: len(list((v/'Briefings').glob('*.md'))) > 0),
]
all_ok = True
for name, fn in checks:
    r = fn()
    print('[OK]' if r else '[!!]', name)
    if not r: all_ok = False
print()
print('READY TO RECORD' if all_ok else 'NOT READY — fix issues above')
"
```

---

## .env Key Groups (Field Names Only)

**Twitter/X (5 keys):**
```
TWITTER_API_KEY
TWITTER_API_SECRET
TWITTER_ACCESS_TOKEN
TWITTER_ACCESS_TOKEN_SECRET
TWITTER_BEARER_TOKEN
```

**Facebook & Instagram (3 keys):**
```
FACEBOOK_PAGE_ID
FACEBOOK_ACCESS_TOKEN
INSTAGRAM_ACCOUNT_ID
```

**LinkedIn (3 keys):**
```
LINKEDIN_EMAIL
LINKEDIN_PASSWORD
HEADLESS
```

**Odoo (4 keys):**
```
ODOO_URL
ODOO_DB
ODOO_USERNAME
ODOO_PASSWORD
```

**SMTP / Email (6 keys):**
```
SMTP_HOST
SMTP_PORT
SMTP_SECURE
SMTP_USER
SMTP_PASS
SMTP_FROM
```

---

## 10-Word Scene Reminders (in order)

| Scene | 10-Word Reminder |
|---|---|
| 1 — Dashboard | Show Dashboard, read queue, explain what AI will do |
| 2 — Queue | Open all 5 files, emphasise Odoo overdue invoice |
| 3 — MCPs | Pan tabs, five servers live, watching Approved folder |
| 4 — Orchestrator | Press Enter, watch skills route, wait TASK_COMPLETE |
| 5 — HITL | Open Odoo draft, approve it, watch MCP fire live |
| 6 — Live Result | Show Odoo invoice created in real ERP system |
| 7 — More HITL | Approve Twitter, show tweet posted, pattern repeats |
| 8 — Audit Log | Open JSON log, read one full entry, all 8 fields |
| 9 — CEO Briefing | Scroll briefing, revenue target, recommendations, zero effort |
| 10 — Architecture Close | Open CLAUDE.md diagram, deliver closing architecture line |

---

*Generated by Claude Code — Gold Tier AI Employee v3.0*
*Briefings/DEMO_RECORDING_GUIDE.md*
