# Silver Tier — Complete Testing & Launch Guide

**Date:** 2026-02-26
**Environment:** Python 3.13.9 · Node.js v24.13.1 · Playwright Chromium ✅

---

## Current System Status (Pre-Test)

| Component | Status | Notes |
|---|---|---|
| Python deps (`uv sync`) | ✅ Ready | 31 packages installed |
| Node deps (`email-mcp`) | ✅ Ready | node_modules present |
| Node deps (`linkedin-mcp`) | ✅ Ready | node_modules present |
| Playwright Chromium | ✅ Ready | v1208 installed |
| `credentials.json` | ✅ Present | Copied from Bronze tier |
| `token.json` | ❌ Missing | Needs one-time Gmail auth (Step 1) |
| `whatsapp_session/` | ✅ Present | Session authenticated |
| `.env` | ✅ Present | Credentials configured |

**One step needed before full launch:** Gmail first-run authorization (Step 1).

---

## Open 4 Terminal Windows

You need 4 terminals open simultaneously, each running one process:

```
Terminal 1: Gmail Watcher (or orchestrator)
Terminal 2: Email MCP Server
Terminal 3: LinkedIn MCP Server
Terminal 4: Claude Reasoning Loop (manual trigger)
```

---

## STEP 0 — Verify Everything Is in Order

Run this first to confirm your environment:

```bash
# Navigate to vault root
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver"

# Confirm Python and uv
uv run python --version
# Expected: Python 3.13.x

# Confirm deps are installed
uv sync
# Expected: "Audited 31 packages"

# Confirm Node
node --version
# Expected: v24.x.x

# Confirm credentials.json
ls credentials.json
# Expected: credentials.json

# Confirm .env
ls .env
# Expected: .env
```

---

## STEP 1 — Gmail First-Run Authorization

**Do this once only.** After this, `token.json` is saved and Gmail runs autonomously.

```bash
# Terminal 1 — Run from vault root
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver"
uv run python gmail_watcher.py
```

**What happens:**
1. A browser window opens automatically
2. Log in to your Google account (if prompted)
3. Click "Allow" to grant Gmail read access
4. Browser closes
5. `token.json` is created in vault root
6. Watcher starts polling Gmail every 120 seconds

**Expected output:**
```
INFO [gmail_watcher] Gmail OAuth2 authorized — token saved to token.json
INFO [gmail_watcher] Starting poll loop (interval: 120s)
INFO [gmail_watcher] Checking Gmail for unread important messages...
```

**If you want to stop it:** `Ctrl+C`
**Token is now saved** — all future runs skip the browser step.

---

## STEP 2 — Start Email MCP Server

**Terminal 2:**

```bash
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver\mcp_servers\email-mcp"
node index.js
```

**Expected output:**
```
[email-mcp] Watching folder: F:\...\silver\Approved
[email-mcp] Email MCP server ready — waiting for approved files...
```

**What this does:** Watches `Approved/` for `EMAIL_REVIEW_*.md` files.
When a file appears, it reads it, sends the email via SMTP, and moves the file to `Done/`.

**To test dry-run (no real email sent):**
```bash
DRY_RUN=true node index.js
```

---

## STEP 3 — Start LinkedIn MCP Server

**Terminal 3:**

```bash
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver\mcp_servers\linkedin-mcp"
node index.js
```

**Expected output:**
```
[linkedin-mcp] Watching folder: F:\...\silver\Approved
[linkedin-mcp] LinkedIn MCP server ready — waiting for approved files...
```

**What this does:** Watches `Approved/` for `LINKEDIN_DRAFT_*.md` files.
When a file appears, it launches Playwright, navigates to LinkedIn, posts the content.

---

## STEP 4 — Run Watchers

### Option A: Run All Watchers via Orchestrator (Recommended)

**Terminal 1:**

```bash
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver"

# Start all watchers + run Claude immediately
uv run python orchestrator.py --now
```

**Flags explained:**
- `--now` → Runs Claude reasoning cycle immediately on startup (instead of waiting until 8 AM)
- No flag → Starts watchers, waits until 8 AM for Claude

**What starts:**
- Gmail watcher (polls every 120s)
- LinkedIn watcher (polls every 300s)
- WhatsApp watcher (polls every 30s)
- Claude reasoning cycle (immediately with `--now`, or scheduled at 8 AM)
- Watchdog supervisor (checks thread health every 30s)

**Expected output:**
```
[orchestrator] Silver AI Employee Orchestrator | Vault: F:\...\silver
[orchestrator] Gmail watcher started (tid=12345)
[orchestrator] LinkedIn watcher started (tid=12346)
[orchestrator] WhatsApp watcher started (tid=12347)
[orchestrator] Scheduled: Claude reasoning loop daily at 08:00 | Watchdog active
[orchestrator] Claude reasoning cycle starting…
```

---

### Option B: Run Individual Watchers (For Testing/Debugging)

```bash
# Gmail watcher only
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver"
uv run python gmail_watcher.py

# LinkedIn watcher only
uv run python linkedin_watcher.py

# WhatsApp watcher only (headed mode — shows browser)
uv run python whatsapp_watcher.py --no-headless

# WhatsApp watcher only (headless — no browser window)
uv run python whatsapp_watcher.py
```

---

## STEP 5 — Trigger Claude Reasoning Loop Manually

**Terminal 4 (or from vault root):**

```bash
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver"

# One-shot Claude run (processes queue and exits)
uv run python orchestrator.py --cron
```

**Or directly via Claude Code CLI:**
```bash
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver"
claude --print "Read CLAUDE.md then run: SKILL_Daily_Briefing → SKILL_Gmail_Triage → SKILL_WhatsApp_Triage → SKILL_LinkedIn_Draft → SKILL_Reasoning_Loop → SKILL_Process_Needs_Action → SKILL_Update_Dashboard. Write TASK_COMPLETE when Needs_Action/ is empty."
```

**Expected output ends with:**
```
TASK_COMPLETE
```

---

## STEP 6 — Test the HITL Approval Workflow

### 6.1 Create a Test Item

```bash
# Create a test email in Needs_Action/
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver"
```

Create `Needs_Action/TEST_EMAIL_Manual_2026-02-26.md`:

```yaml
---
type: email
status: pending
created: 2026-02-26T10:00:00Z
source: gmail
message_id: test_manual_001
sender_email: newclient@example.com
sender_name: New Test Client
subject: "Interested in your AI consulting services"
---

# Email: Interested in your AI consulting services

**From:** New Test Client <newclient@example.com>
**Subject:** Interested in your AI consulting services

Hi,

I came across your profile and I'm very interested in discussing your AI consulting services.

Could we schedule a 30-minute call this week to discuss further?

Best regards,
New Test Client
```

### 6.2 Run Claude to Process It

```bash
uv run python orchestrator.py --cron
```

### 6.3 Verify HITL Was Triggered

```bash
# Check Pending_Approval/ for the escalated item
ls "Pending_Approval/"
# Expected: A new EMAIL_REVIEW_*.md or NEW_CONTACT_REVIEW_*.md file
```

### 6.4 Approve the Item

1. Open `Pending_Approval/NEW_CONTACT_REVIEW_*.md` in Obsidian or any text editor
2. Review the draft reply
3. Move the file to `Approved/` folder:

```bash
# Windows PowerShell alternative
mv "Pending_Approval/NEW_CONTACT_REVIEW_New_Test_Client_2026-02-26.md" "Approved/"
```

### 6.5 Watch Email MCP Send It

Switch to Terminal 2 (email-mcp). You should see:

```
[email-mcp] New file detected: Approved/NEW_CONTACT_REVIEW_New_Test_Client_2026-02-26.md
[email-mcp] Sending email to: newclient@example.com
[email-mcp] Email sent successfully
[email-mcp] Moving file to Done/
```

---

## STEP 7 — Test LinkedIn Post Flow

### 7.1 Check Existing LinkedIn Draft

There is already a LinkedIn draft in `Pending_Approval/`:
```
Pending_Approval/LINKEDIN_DRAFT_Consulting_Services_2026-02-26.md
```

### 7.2 Approve and Watch LinkedIn MCP Post

```bash
# Move to Approved
mv "Pending_Approval/LINKEDIN_DRAFT_Consulting_Services_2026-02-26.md" "Approved/"
```

Switch to Terminal 3 (linkedin-mcp). You should see:

```
[linkedin-mcp] New file detected: Approved/LINKEDIN_DRAFT_Consulting_Services_2026-02-26.md
[linkedin-mcp] Launching browser...
[linkedin-mcp] Navigating to LinkedIn...
[linkedin-mcp] Posting content...
[linkedin-mcp] Post published successfully
[linkedin-mcp] Moving file to Done/
```

---

## STEP 8 — Test WhatsApp Watcher

### 8.1 Check WhatsApp Session Status

```bash
ls "whatsapp_session/"
# Should show browser session files (Default folder, etc.)
```

### 8.2 Start WhatsApp Watcher Headed (Verify Session)

```bash
uv run python whatsapp_watcher.py --no-headless
```

**Expected:** Browser opens, shows WhatsApp Web **already logged in** (session restored).
If it shows QR code, scan it with your phone.

### 8.3 Test Keyword Filtering

Send a WhatsApp message to yourself (or have someone send one) containing keywords like:
- "invoice"
- "payment"
- "urgent"
- "hello" or any configured keyword

The watcher should detect it and write a file to `Needs_Action/`.

---

## STEP 9 — Run Full System Integration Test

This runs all 6 components together:

**Terminal 1 — Full Orchestrator (watchers + schedule):**
```bash
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver"
uv run python orchestrator.py --now
```

**Terminal 2 — Email MCP:**
```bash
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver\mcp_servers\email-mcp"
node index.js
```

**Terminal 3 — LinkedIn MCP:**
```bash
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver\mcp_servers\linkedin-mcp"
node index.js
```

Wait 2-3 minutes for watchers to poll their channels. Then observe:
- New files appearing in `Needs_Action/`
- Claude processing them (if `--now` was used)
- Items moving through the pipeline

---

## STEP 10 — Verify Dashboard Updates

After any Claude cycle:

```bash
# Check Dashboard.md was updated
cat Dashboard.md
# Verify: "Last Updated" timestamp is recent
# Verify: Queue counts are accurate
# Verify: Activity log has new entries
```

---

## Feature-by-Feature Test Checklist

| Feature | Test | Expected Result | Status |
|---|---|---|---|
| Gmail OAuth | Run `gmail_watcher.py` | Browser auth → token.json created | ⬜ |
| Gmail Polling | Wait 120s after auth | Emails appear in Needs_Action/ | ⬜ |
| LinkedIn Watcher | Run `linkedin_watcher.py` | Notifications in Needs_Action/ or Done/ | ⬜ |
| WhatsApp Watcher | Run `whatsapp_watcher.py --no-headless` | Session restored, monitoring | ⬜ |
| Claude Triage | Run `orchestrator.py --cron` | Items moved to Done/ or Pending_Approval/ | ⬜ |
| HITL Trigger | New contact email → Claude processes | File in Pending_Approval/ | ⬜ |
| Email MCP | Move approval to Approved/ | Email sent, file moved to Done/ | ⬜ |
| LinkedIn MCP | Move LinkedIn draft to Approved/ | Post published, file moved to Done/ | ⬜ |
| Plan Creation | Complex task in Needs_Action/ | Plan created in In_Progress/ | ⬜ |
| Dashboard Update | After any Claude cycle | Dashboard.md updated with timestamp | ⬜ |
| Orchestrator | Run `orchestrator.py` | All watchers + schedule started | ⬜ |
| Watchdog | Kill a watcher thread | Watchdog restarts it within 30s | ⬜ |
| TASK_COMPLETE | Empty queue Claude run | Output ends with TASK_COMPLETE | ⬜ |

---

## Quick Reference — All Commands

```bash
# ── SETUP (once) ────────────────────────────────────────────────────────────
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver"
uv sync                                    # Install Python deps

# ── STEP 1: Gmail Auth (once) ────────────────────────────────────────────────
uv run python gmail_watcher.py             # Browser opens → authorize → token saved

# ── STEP 2: MCP Servers (keep running) ──────────────────────────────────────
cd mcp_servers/email-mcp && node index.js  # Terminal 2
cd mcp_servers/linkedin-mcp && node index.js  # Terminal 3

# ── STEP 3: Full System (keep running) ──────────────────────────────────────
cd "F:\Hackathon 0 Personal AI Employee\AI_Employee_Vault\silver"
uv run python orchestrator.py --now        # Terminal 1 — all watchers + immediate Claude

# ── MANUAL TRIGGERS ─────────────────────────────────────────────────────────
uv run python orchestrator.py --cron       # One-shot Claude run
uv run python orchestrator.py --now        # Start watchers + immediate Claude run

# ── INDIVIDUAL WATCHERS ─────────────────────────────────────────────────────
uv run python gmail_watcher.py             # Gmail only
uv run python linkedin_watcher.py          # LinkedIn only
uv run python whatsapp_watcher.py          # WhatsApp headless
uv run python whatsapp_watcher.py --no-headless  # WhatsApp with browser visible
```

---

## Common Issues & Fixes

| Issue | Symptom | Fix |
|---|---|---|
| `token.json` missing | Gmail watcher opens browser every time | Complete Step 1 authorization |
| LinkedIn 2FA prompt | LinkedIn watcher gets stuck | Log in manually once in headed mode |
| WhatsApp QR shown | Session expired | Scan QR with phone |
| `claude.cmd` not found | Orchestrator Claude cycle fails | Confirm Claude Code is in PATH |
| Email not sent | email-mcp shows error | Check SMTP credentials in `.env` |
| Port already in use | MCP server won't start | Kill old process: `taskkill /F /IM node.exe` |
| Import error | watcher fails to start | Run `uv sync` again |

---

## Recommended Demo Sequence (5 Minutes)

1. **(1 min)** Show vault structure in Obsidian — explain folder pipeline
2. **(1 min)** Start orchestrator (`--now`) — show watchers launching
3. **(1 min)** Show `Pending_Approval/` — 4 items waiting for approval
4. **(1 min)** Move `EMAIL_REVIEW_*.md` to `Approved/` — watch email-mcp send it
5. **(1 min)** Show `Dashboard.md` — point out activity log, queue counts, reasoning

---

*Silver Tier AI Employee — Complete Testing Guide*
*All components verified: Python 3.13.9 · Node.js v24.13.1 · Playwright Chromium v1208*
