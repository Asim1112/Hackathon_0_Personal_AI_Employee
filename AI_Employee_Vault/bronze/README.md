# Bronze Tier — Personal AI Employee

> Hackathon 0 · 2026 · Built with Claude Code

A fully autonomous AI Employee that monitors your Gmail, triages incoming emails using business rules, drafts replies, and maintains a live business dashboard — all inside an Obsidian vault.

---

## Architecture

```
Gmail API → gmail_watcher.py → Needs_Action/ → Claude Code → Done/
                                      ↓
                            Company_Handbook.md (rules)
                            Dashboard.md (live state)
```

**Perception Layer** — `gmail_watcher.py` polls Gmail every 120s for unread important emails and writes structured `.md` files to `Needs_Action/`.

**Reasoning Layer** — Claude Code reads the queue, applies `Company_Handbook.md` rules, triages emails, drafts replies, and moves files to `Done/`.

**Memory Layer** — `Dashboard.md` is the real-time nerve center. `Done/` is the audit trail.

---

## Folder Structure

```
bronze/
├── Inbox/                    ← Draft replies (never sent automatically)
├── Needs_Action/             ← Watcher writes here, Claude reads from here
├── Done/                     ← Processed items with full audit trail
├── Pending_Approval/         ← Sensitive items requiring human sign-off
├── skills/
│   ├── SKILL_Gmail_Triage.md           ← Email classification skill
│   └── SKILL_Process_Needs_Action.md   ← Queue processing skill
├── .claude/
│   ├── hooks/stop_hook.py    ← Ralph Wiggum Stop hook
│   └── settings.json         ← Hook registration
├── Dashboard.md              ← Live business status
├── Company_Handbook.md       ← Rules of Engagement
├── CLAUDE.md                 ← Claude Code operating instructions
├── Plan.md                   ← Implementation roadmap
├── base_watcher.py           ← Abstract watcher base class
├── gmail_watcher.py          ← Gmail API watcher
├── ralph_loop.sh             ← Autonomous loop launcher
└── pyproject.toml            ← Python dependencies
```

---

## Bronze Tier Deliverables (Hackathon Requirements)

| Requirement | Status |
|---|---|
| Obsidian vault with Dashboard.md and Company_Handbook.md | ✅ |
| One working Watcher script (Gmail) | ✅ |
| Claude Code reading from and writing to the vault | ✅ |
| Basic folder structure: /Inbox, /Needs_Action, /Done | ✅ |
| All AI functionality as Agent Skills | ✅ |

---

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Set up Gmail API credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → Enable **Gmail API**
3. Create **OAuth 2.0 Client ID** (Desktop app type)
4. Download as `credentials.json` → place in this directory
5. Add your Gmail as a Test User in OAuth consent screen

### 3. Run the Gmail Watcher

```bash
uv run python gmail_watcher.py
```

First run opens a browser for OAuth consent. `token.json` is saved automatically — subsequent runs need no browser.

### 4. Process the queue with Claude Code

Open Claude Code in this directory and run:

```
Read CLAUDE.md, then use SKILL_Gmail_Triage and SKILL_Process_Needs_Action
to process all files in Needs_Action/. Update Dashboard.md when done.
```

### 5. (Optional) Autonomous loop

```bash
bash ralph_loop.sh --max-iterations 5
```

---

## Agent Skills

| Skill | Purpose |
|---|---|
| `SKILL_Gmail_Triage` | Classifies emails: ESCALATE / DRAFT_REPLY / LOG_ONLY / HUMAN_REVIEW |
| `SKILL_Process_Needs_Action` | Processes the full queue, writes audit notes, moves to Done/ |

---

## Key Rules (from Company_Handbook.md)

- Payments over £500 → written to `Pending_Approval/` for human sign-off
- Legal/complaint keywords → auto-escalated, never handled autonomously
- All replies are **drafts only** — nothing is sent automatically (Bronze tier)
- `Dashboard.md` is updated after every processing cycle

---

## Ralph Wiggum Loop

The autonomous loop re-injects the task prompt after each Claude response until `Needs_Action/` is empty or max iterations is reached.

```bash
bash ralph_loop.sh "Process all files in Needs_Action" --max-iterations 5
```

The `.claude/hooks/stop_hook.py` implements the same pattern natively for interactive Claude Code sessions.

---

## Files Not Committed

```
credentials.json          ← Google OAuth client secret (sensitive)
token.json                ← Your personal access token (sensitive)
.gmail_watcher_state.json ← Watcher runtime state
.venv/                    ← Python virtual environment
```

---

*Bronze Tier · Personal AI Employee Hackathon 0 · Built with Claude Code*
