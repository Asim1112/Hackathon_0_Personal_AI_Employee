# 🥇 Personal AI Employee — Gold Tier

> **Hackathon 0 · 2026** — Building Autonomous FTEs with Claude Code

A fully autonomous AI Employee that triages email, manages invoicing in Odoo ERP, drafts social media content across five platforms, and delivers a weekly CEO briefing — all with a strict **Human-in-the-Loop (HITL)** approval gate on every external action.

---

## 🎬 Demo Video

[![Personal AI Employee — Gold Tier Demo](https://img.youtube.com/vi/oVS4CmAxPw8/maxresdefault.jpg)](https://youtu.be/oVS4CmAxPw8)

**[▶ Watch the 13-minute demo on YouTube](https://youtu.be/oVS4CmAxPw8)**

> Recorded live — all posts, invoices, and emails shown are real. No mock data.

---

## Overview

The Personal AI Employee is built in three tiers:

| Tier | Capabilities |
|------|-------------|
| 🥉 Bronze | File watcher, basic triage, Obsidian vault |
| 🥈 Silver | Gmail, LinkedIn, WhatsApp, MCP servers for email + LinkedIn |
| 🥇 **Gold** | **+ Odoo ERP, Twitter/X, Facebook, Instagram, audit logging, weekly CEO briefing** |

Gold Tier turns Claude Code into a reasoning layer that monitors 6 live channels, drafts responses and actions, routes everything through a human approval gate, and executes only after explicit sign-off.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   PERCEPTION LAYER                  │
│  Gmail   LinkedIn   WhatsApp   Twitter   Facebook   │
│                     Odoo ERP                        │
│              (6 Python Watchers)                    │
└──────────────────────┬──────────────────────────────┘
                       │ writes .md files
                       ▼
              ┌─────────────────┐
              │  Needs_Action/  │  ← Queue
              └────────┬────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                  REASONING LAYER                    │
│              Claude Code (you invoke)               │
│   Reads Company_Handbook.md + Business_Goals.md     │
│   Applies 13 Agent Skills                           │
│   Drafts replies, posts, invoices, briefings        │
└──────────────────────┬──────────────────────────────┘
                       │ writes drafts
                       ▼
         ┌─────────────────────────┐
         │    Pending_Approval/    │  ← HITL Gate
         └────────────┬────────────┘
                      │ human moves to Approved/
                      ▼
┌─────────────────────────────────────────────────────┐
│                   ACTION LAYER                      │
│  email-mcp   odoo-mcp   twitter-mcp   linkedin-mcp  │
│              facebook-instagram-mcp                 │
│              (5 Node.js MCP Servers)                │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
      Gmail · Odoo · Twitter · LinkedIn · Facebook/Instagram
```

**Key principle:** Claude never executes actions directly. Every output is a draft. A human approves. The MCP server executes.

---

## Folder Structure

```
gold/
│
├── CLAUDE.md                    # Operating instructions for Claude Code (read first)
├── Dashboard.md                 # Real-time vault state — updated each cycle
├── Business_Goals.md            # Revenue targets, KPIs, service rates
├── Company_Handbook.md          # Business rules, HITL policy, voice & tone
│
├── Needs_Action/                # Incoming queue — watchers write here
├── Inbox/                       # Email draft replies — move to Approved/ to send
├── Pending_Approval/            # HITL gate — all drafts wait here
├── Approved/                    # Human-approved — MCP servers watch this
├── Done/                        # Completed items — full audit trail
├── Rejected/                    # Rejected or failed items
├── Plans/                       # Multi-step reasoning plans (complex tasks)
├── In_Progress/                 # Plans currently being executed
│
├── Briefings/                   # Weekly CEO briefings (auto-generated Sunday 23:00)
├── Accounting/                  # Odoo financial summaries and invoice records
├── Logs/                        # Structured JSON audit trail (YYYY-MM-DD.json)
├── Social_Analytics/            # Twitter + Facebook/Instagram performance summaries
│
├── skills/                      # 13 Agent Skills — Claude's task instructions
│   ├── SKILL_Gmail_Triage.md
│   ├── SKILL_WhatsApp_Triage.md
│   ├── SKILL_LinkedIn_Draft.md
│   ├── SKILL_Twitter_Draft.md           # Gold new
│   ├── SKILL_Facebook_Instagram.md      # Gold new
│   ├── SKILL_Odoo_Accounting.md         # Gold new
│   ├── SKILL_Weekly_CEO_Briefing.md     # Gold new
│   ├── SKILL_Audit_Logger.md            # Gold new
│   ├── SKILL_Daily_Briefing.md
│   ├── SKILL_Update_Dashboard.md
│   ├── SKILL_Reasoning_Loop.md
│   ├── SKILL_HITL_Approval.md
│   └── SKILL_Process_Needs_Action.md
│
├── mcp_servers/                 # 5 Node.js MCP servers — execute approved actions
│   ├── email-mcp/               # Sends email via Gmail SMTP
│   ├── linkedin-mcp/            # Posts to LinkedIn via Playwright (persistent context)
│   ├── odoo-mcp/                # Creates invoices in Odoo via JSON-RPC   [Gold]
│   ├── twitter-mcp/             # Posts tweets via Twitter API v2          [Gold]
│   └── facebook-instagram-mcp/  # Posts via Meta Graph API                 [Gold]
│
├── gmail_watcher.py             # Polls Gmail via OAuth2 API
├── linkedin_watcher.py          # Polls LinkedIn via Playwright
├── whatsapp_watcher.py          # Polls WhatsApp Web via Playwright
├── twitter_watcher.py           # Polls Twitter/X via tweepy               [Gold]
├── facebook_watcher.py          # Polls Facebook + Instagram via httpx      [Gold]
├── odoo_watcher.py              # Polls Odoo via JSON-RPC                   [Gold]
├── base_watcher.py              # Abstract base class for all watchers
├── orchestrator.py              # Supervisor — starts all watchers + scheduler
├── audit_logger.py              # Shared JSON logging utility               [Gold]
├── retry_handler.py             # Exponential backoff decorator             [Gold]
│
├── docker/
│   └── odoo/
│       ├── docker-compose.yml   # Odoo + PostgreSQL 16
│       └── config/odoo.conf
│
├── pyproject.toml               # Python dependencies (managed by uv)
├── .env.example                 # Environment variable template (copy to .env)
└── .gitignore                   # Excludes .env, credentials, node_modules
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Claude Code](https://claude.ai/code) | Latest | AI reasoning layer |
| Python | 3.11+ | Watchers + orchestrator |
| [uv](https://docs.astral.sh/uv/) | Latest | Python package manager |
| Node.js | 18+ | MCP servers |
| Docker Desktop | Latest | Odoo ERP |
| Obsidian | Latest | Vault viewer (optional) |

---

## Setup Instructions

### 1. Enter the Gold Vault

```bash
cd AI_Employee_Vault/gold
```

### 2. Install Python Dependencies

```bash
uv sync
```

### 3. Install MCP Server Dependencies

```bash
cd mcp_servers/email-mcp && npm install && cd ../..
cd mcp_servers/linkedin-mcp && npm install && npx playwright install chromium && cd ../..
cd mcp_servers/odoo-mcp && npm install && cd ../..
cd mcp_servers/twitter-mcp && npm install && cd ../..
cd mcp_servers/facebook-instagram-mcp && npm install && cd ../..
```

> **LinkedIn:** `npx playwright install chromium` is required. The LinkedIn MCP uses Playwright browser automation with a persistent Chromium profile stored in `mcp_servers/linkedin-mcp/.browser_profile/`. No manual session setup is needed — the browser logs in automatically on first use and reuses the saved profile on subsequent runs.

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials — see [Environment Variables](#environment-variables) below.

### 5. Start Odoo via Docker

```bash
cd docker/odoo
docker compose up -d
```

Open [http://localhost:8069](http://localhost:8069), create a database named `ai_employee`, and install the **Accounting** module.

### 6. Authenticate Gmail (OAuth2)

Run once to authorise Gmail access:

```bash
uv run python gmail_watcher.py --auth
```

A browser opens. Sign in and grant access. A `token.json` file is created locally (excluded from git).

### 7. Authenticate WhatsApp

```bash
uv run python whatsapp_watcher.py --auth
```

Scan the QR code with WhatsApp on your phone. The session is saved to `whatsapp_session/` (excluded from git).

### 8. Start Everything

Open **6 terminals** in the `gold/` directory:

| Terminal | Command | Purpose |
|----------|---------|---------|
| T1 | `node mcp_servers/email-mcp/index.js` | Email sender |
| T2 | `node mcp_servers/linkedin-mcp/index.js` | LinkedIn poster |
| T3 | `node mcp_servers/odoo-mcp/index.js` | Odoo invoice creator |
| T4 | `node mcp_servers/twitter-mcp/index.js` | Twitter poster |
| T5 | `node mcp_servers/facebook-instagram-mcp/index.js` | Facebook/Instagram poster |
| T6 | `uv run python orchestrator.py` | Watcher supervisor |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
# ── Gmail (SMTP — for email-mcp) ──────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your.email@gmail.com
SMTP_PASS=your-gmail-app-password      # 16-char App Password from myaccount.google.com/apppasswords
SMTP_FROM="Your Name <your.email@gmail.com>"

# ── LinkedIn ──────────────────────────────────────────────────────────────────
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your-linkedin-password
HEADLESS=false                         # false = browser visible on screen (recommended for demo)

# ── Twitter / X ───────────────────────────────────────────────────────────────
TWITTER_API_KEY=your-api-key
TWITTER_API_SECRET=your-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-access-token-secret
TWITTER_BEARER_TOKEN=your-bearer-token
TWITTER_DEMO_MODE=false                # Set to true if your API tier doesn't support write access (402)

# ── Facebook & Instagram ──────────────────────────────────────────────────────
FACEBOOK_PAGE_ID=your-page-id
FACEBOOK_ACCESS_TOKEN=your-page-access-token   # Page Access Token from Meta Graph API Explorer
INSTAGRAM_ACCOUNT_ID=your-instagram-business-account-id

# ── Odoo (self-hosted) ────────────────────────────────────────────────────────
ODOO_URL=http://localhost:8069
ODOO_DB=ai_employee
ODOO_USERNAME=admin
ODOO_PASSWORD=your-odoo-admin-password

# ── Watcher Intervals (seconds) ───────────────────────────────────────────────
GMAIL_INTERVAL=120
LINKEDIN_INTERVAL=300
WHATSAPP_INTERVAL=30
TWITTER_INTERVAL=300
FACEBOOK_INTERVAL=600
ODOO_INTERVAL=600
```

> **Gmail App Password:** Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requires 2-Step Verification enabled). Create a new app password and paste the 16-character code into `SMTP_PASS`.

> **Twitter:** Requires a developer account at [developer.twitter.com](https://developer.twitter.com) with an app that has **OAuth 1.0a Read+Write** permissions. If your free-tier account returns a `402` error on posting, set `TWITTER_DEMO_MODE=true` — the MCP will complete the full workflow and log the action without hitting the paid endpoint.

> **Facebook Page Access Token:** Expires after ~1 hour for short-lived tokens. Generate a fresh one in [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/) 30 minutes before use.

> **Instagram:** Must be a Business or Creator account linked to your Facebook Page. Find your `INSTAGRAM_ACCOUNT_ID` by calling `GET /{page-id}?fields=instagram_business_account` in Graph API Explorer with your Page Access Token.

---

## Running the Claude Reasoning Loop

Claude Code is the reasoning layer. Invoke it manually or on a schedule.

### Recommended Daily Prompt

```
Read CLAUDE.md, skills/SKILL_Gmail_Triage.md, skills/SKILL_Odoo_Accounting.md,
and skills/SKILL_Twitter_Draft.md.

Process all items in Needs_Action/. Strictly follow each skill's exact file
format including all frontmatter fields and ```json action blocks.

Write TASK_COMPLETE when done.
```

### Automated Schedule (via orchestrator.py)

| Trigger | When | What happens |
|---------|------|-------------|
| Daily triage | 08:00 every day | Claude processes Needs_Action/ |
| Weekly briefing | Sunday 23:00 | CEO briefing generated to Briefings/ |
| Watcher poll | Continuous | All 6 channels monitored |

```bash
# Run orchestrator with an immediate Claude cycle on start
uv run python orchestrator.py --now

# One-shot daily cycle (for cron)
uv run python orchestrator.py --cron

# Generate weekly CEO briefing now
uv run python orchestrator.py --briefing
```

---

## Odoo Integration

Gold Tier connects Claude Code to a self-hosted **Odoo** instance via JSON-RPC.

### What Claude Can Do

| Action | Description |
|--------|-------------|
| `create_invoice` | Creates a draft customer invoice with line items |
| `confirm_invoice` | Confirms a draft invoice — requires approval |
| `sync_accounting` | Pulls outstanding invoices and AR summary |

### Invoice Flow

```
Odoo watcher detects new project/expense
    ↓
Writes ODOO_*.md to Needs_Action/
    ↓
Claude drafts ODOO_REVIEW_*.md using SKILL_Odoo_Accounting.md
    ↓
File lands in Pending_Approval/ (never sent without human sign-off)
    ↓
Human reviews → moves to Approved/
    ↓
odoo-mcp creates draft invoice in Odoo at http://localhost:8069
    ↓
Human opens Odoo → reviews → posts manually
```

All invoices are created in **draft** state. Claude never confirms or posts an invoice without a second explicit human approval.

### Required Action JSON in Odoo Draft Files

```json
{
  "partner_name": "Client Name",
  "partner_email": "client@example.com",
  "invoice_date": "2026-03-14",
  "lines": [
    { "name": "AI Consulting", "quantity": 10, "price_unit": 150 }
  ],
  "ref": "PROJECT-001"
}
```

---

## Social Media Pipeline

### Twitter / X

Claude drafts replies and posts using `SKILL_Twitter_Draft.md`. Every draft file must include:

```yaml
---
type: social_draft
platform: twitter
send_via_mcp: twitter-mcp
action: post_tweet
status: pending
char_count: 268
---
```

Plus a JSON action block at the bottom of the file body:

```json
{
  "content": "Your tweet text here (max 280 chars)"
}
```

For replies to mentions:

```json
{
  "action": "reply_tweet",
  "reply_to_tweet_id": "1234567890",
  "content": "Your reply text here"
}
```

> **Twitter API write access:** Requires OAuth 1.0a with Read+Write permissions. If your account returns a `402 Payment Required` error, set `TWITTER_DEMO_MODE=true` in `.env` — the MCP logs the action and moves the file to `Done/` without calling the API.

### Facebook

Claude drafts Facebook Business Page posts using `SKILL_Facebook_Instagram.md`. Required frontmatter:

```yaml
---
type: social_post
platform: facebook
send_via_mcp: facebook-instagram-mcp
action: post_facebook
status: pending
---
```

Required JSON action block:

```json
{
  "message": "Your post text here"
}
```

The `facebook-instagram-mcp` posts directly to your Facebook Page via `POST /{page-id}/feed` on the Meta Graph API v19.0.

### Instagram

Instagram requires a **Business or Creator account** linked to your Facebook Page, and every post **must include an image URL**. The MCP uses Meta's two-step container/publish flow.

Required frontmatter:

```yaml
---
type: social_post
platform: instagram
send_via_mcp: facebook-instagram-mcp
action: post_instagram
image_url: https://example.com/your-image.jpg   # required — post will be rejected without this
status: pending
---
```

Required JSON action block:

```json
{
  "caption": "Your caption with #hashtags",
  "image_url": "https://example.com/your-image.jpg"
}
```

The MCP executes two API calls:
1. `POST /{instagram-account-id}/media` — creates the media container
2. `POST /{instagram-account-id}/media_publish` — publishes the container to the profile

> **Image URL:** Must be a publicly accessible HTTPS URL. The image is fetched by Instagram's servers, so local or localhost URLs will fail. Use a public hosting service (e.g. Imgur, PostImg, or your own CDN).

---

## Human-in-the-Loop (HITL) Approval Gate

**Nothing executes without human approval.** This is non-negotiable by design.

### Mandatory HITL Triggers

| Trigger | Action |
|---------|--------|
| Any social media post | → `Pending_Approval/` before posting |
| Any email to a new contact | → `Pending_Approval/` before sending |
| Any payment or invoice | → `Pending_Approval/` if over £50 |
| Any Odoo action | → `Pending_Approval/` always |
| Negative mentions / complaints | → `Pending_Approval/` always |
| Legal or compliance language detected | → `Pending_Approval/` always |

### Approval Flow

```
Pending_Approval/DRAFT_*.md
       │
       ├── Human approves → moves to Approved/
       │         └── MCP server fires → executes → Done/
       │
       └── Human rejects → moves to Rejected/
                   └── Action discarded
```

MCP servers watch `Approved/` using `chokidar`. The moment a file lands there, the relevant server executes and moves the file to `Done/`.

---

## Weekly CEO Briefing

Every **Sunday at 23:00**, the orchestrator triggers `SKILL_Weekly_CEO_Briefing.md`.

Claude generates a structured report to `Briefings/CEO_BRIEFING_YYYY-MM-DD.md` covering:

- Revenue this week vs target (pulled from Odoo)
- Outstanding invoices older than 14 days
- SLA breaches (emails unanswered > 48h)
- Social media activity (posts, engagement across all 5 platforms)
- New leads captured this week
- Pending approvals older than 24h (bottleneck flags)
- Subscription audit (tools unused > 30 days)
- Proactive recommendations

Trigger manually at any time:

```bash
uv run python orchestrator.py --briefing
```

---

## Audit Logging

Every action Claude takes is appended to `Logs/YYYY-MM-DD.json`. Each entry has eight fields:

```json
{
  "timestamp": "2026-03-14T10:30:00Z",
  "action_type": "email_draft_created",
  "actor": "claude_code",
  "target": "EMAIL_2026-03-14_Client_Status_Update.md",
  "skill_used": "SKILL_Gmail_Triage",
  "approval_status": "pending",
  "result": "escalated",
  "notes": "Draft reply written to Inbox/. Sarah Johnson, TechCorp — board deadline Friday."
}
```

Run `SKILL_Audit_Logger` at the end of each Claude cycle to ensure a complete trail.

---

## Agent Skills Reference

| Skill | Channel | Output Location |
|-------|---------|----------------|
| `SKILL_Gmail_Triage` | Email | `Inbox/` or `Pending_Approval/` |
| `SKILL_WhatsApp_Triage` | WhatsApp | `Inbox/` or `Pending_Approval/` |
| `SKILL_LinkedIn_Draft` | LinkedIn | `Pending_Approval/` |
| `SKILL_Twitter_Draft` | Twitter/X | `Pending_Approval/` |
| `SKILL_Facebook_Instagram` | Facebook + Instagram | `Pending_Approval/` |
| `SKILL_Odoo_Accounting` | Odoo ERP | `Pending_Approval/` |
| `SKILL_Weekly_CEO_Briefing` | All channels | `Briefings/` |
| `SKILL_Audit_Logger` | All | `Logs/YYYY-MM-DD.json` |
| `SKILL_Update_Dashboard` | Vault state | `Dashboard.md` |
| `SKILL_Daily_Briefing` | Scheduled | `Inbox/` |
| `SKILL_Reasoning_Loop` | Complex tasks | `Plans/` → `In_Progress/` → `Done/` |
| `SKILL_HITL_Approval` | Any flagged item | `Pending_Approval/` |
| `SKILL_Process_Needs_Action` | Queue dispatcher | Routes to correct skill |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Email MCP skips file | `type:` field missing or wrong | Ensure `type: draft_reply` in frontmatter |
| Email MCP — no `to` field | Claude omitted recipient | Ensure `to: email@address.com` in frontmatter |
| Twitter MCP rejects file | No JSON action block | Add ` ```json ` block with `content` field |
| Twitter MCP — `402` error | Free-tier API doesn't allow write | Set `TWITTER_DEMO_MODE=true` in `.env` |
| Odoo MCP 401 error | Wrong Odoo credentials | Check `ODOO_PASSWORD` in `.env` |
| Twitter MCP 401 error | Missing Twitter API keys | Set all `TWITTER_API_*` and `TWITTER_ACCESS_TOKEN*` keys in `.env` |
| Gmail OAuth failure | `token.json` expired | Run `uv run python gmail_watcher.py --auth` again |
| Odoo not reachable | Docker not running | `cd docker/odoo && docker compose up -d` |
| MCP skips file silently | `send_via_mcp:` mismatch | Value must match MCP server name exactly (case-sensitive) |
| Claude writes wrong format | Skill file not read | Add skill filename explicitly to the Claude prompt |
| LinkedIn `#username` timeout | Bot detection on login | Delete `.browser_profile/` and retry; persistent context accumulates trust over runs |
| LinkedIn editor not found | LinkedIn UI update | Check CSS selectors in `linkedin-mcp/index.js` match current DOM |
| Instagram post rejected | No `image_url` in file | Instagram requires a public HTTPS image URL — add `image_url` to frontmatter and JSON block |
| Instagram `image_url` fails | Private/localhost URL | Use a publicly accessible URL; Instagram's servers must be able to fetch the image |
| Facebook `#190` token error | Page Access Token expired | Generate a fresh token in Meta Graph API Explorer and update `FACEBOOK_ACCESS_TOKEN` in `.env` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Reasoning | [Claude Code](https://claude.ai/code) (claude-sonnet-4-6) |
| Watchers | Python 3.11+, tweepy, httpx, Playwright, google-api-python-client |
| MCP Servers | Node.js 18+, nodemailer, twitter-api-v2, chokidar, xmlrpc |
| ERP | Odoo Community + PostgreSQL 16 (Docker) |
| LinkedIn Automation | Playwright `launchPersistentContext` — persistent Chromium profile |
| Social APIs | Twitter API v2, Meta Graph API v19.0 |
| Vault / Memory | Obsidian (markdown files) |
| Package Management | uv (Python), npm (Node.js) |

---

## Related Tiers

| Tier | Folder | README |
|------|--------|--------|
| 🥉 Bronze | `bronze/` | [Bronze README](../bronze/README.md) |
| 🥈 Silver | `silver/` | [Silver README](../silver/README.md) |
| 🥇 Gold | `gold/` | You are here |

---

## Built For

**Hackathon 0: Building Autonomous FTEs in 2026**

> Human strategy. AI execution. That's the future of lean consulting.

---

*Gold Tier — Personal AI Employee · Built with Claude Code · 2026*
