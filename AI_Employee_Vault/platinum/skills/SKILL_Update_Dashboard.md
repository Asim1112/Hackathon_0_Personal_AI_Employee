---
skill: update_dashboard
version: 1.0
tier: silver
trigger: manual | auto (called at end of every processing cycle)
inputs:
  - All vault folders (count files in each)
  - Recent activity log (what was processed this cycle)
outputs:
  - Dashboard.md fully refreshed with current state
reads:
  - Inbox/*.md
  - Needs_Action/*.md
  - Done/*.md (today's entries)
  - Pending_Approval/*.md
  - Approved/*.md
  - Rejected/*.md
  - Plans/*.md
  - In_Progress/*.md
writes:
  - Dashboard.md (all sections)
created: 2026-02-25
---

# SKILL: Update Dashboard (Silver Tier)

## What This Skill Does

Performs a full refresh of `Dashboard.md` to reflect the current true state of
the vault. Run this at the end of every processing cycle and after any significant action.

This skill is called by other skills (SKILL_Process_Needs_Action, SKILL_Daily_Briefing)
and can also be invoked standalone.

---

## When to Run This Skill

Run this skill:
- After every processing cycle (end of SKILL_Process_Needs_Action)
- After SKILL_Daily_Briefing completes
- After any HITL approval/rejection changes the vault state
- When the user asks to "refresh the dashboard" or "update the status"

---

## Step-by-Step Instructions

### Step 1 — Count all folder contents

For each folder, count `.md` files with the relevant status:

| Folder | What to count |
|---|---|
| `Inbox/` | All .md files |
| `Needs_Action/` | Files with `status: pending` |
| `Plans/` | Files with `status: pending` |
| `In_Progress/` | Files with `status: in_progress` |
| `Pending_Approval/` | Files with `status: pending` |
| `Done/` | Files with `processed_at` today (today's date) |

---

### Step 2 — Rewrite System Status table

```markdown
## System Status

| Field                  | Value                                    |
|------------------------|------------------------------------------|
| Last Updated           | <current ISO timestamp>                  |
| Gmail Watcher          | <✅ Running (120s) | ⚪ Not running>     |
| LinkedIn Watcher       | <✅ Running (300s) | ⚪ Not running>     |
| Claude Status          | ✅ Processing complete                    |
| Scheduler              | <✅ Active | ⚪ Not configured>         |
| Items in Inbox         | <N>                                      |
| Items Needs Action     | <N>                                      |
| Items in Plans         | <N>                                      |
| Items In_Progress      | <N>                                      |
| Items Done Today       | <N>                                      |
| Pending Approvals      | <N>                                      |
```

---

### Step 3 — Rewrite Pending Messages table

List all email items still in `Needs_Action/` or recently processed:

```markdown
## Pending Messages

| # | Source | From | Subject / Preview | Received | Priority |
|---|--------|------|-------------------|----------|----------|
| 1 | gmail  | Name | Subject | 2026-02-25 | 🔴 urgent |
```

If queue is clear: `| — | — | Queue cleared — all emails processed | — | — |`

---

### Step 4 — Rewrite Plans & In Progress table

```markdown
## Plans & In Progress

| File | Goal | Status | Steps Done | Steps Total |
|------|------|--------|------------|-------------|
| PLAN_<slug>.md | <goal> | in_progress | 2 | 6 |
```

If empty: `| — No active plans — | — | — | — | — |`

---

### Step 5 — Rewrite Pending Approvals table

```markdown
## Pending Approvals

| File | Action | Amount/Value | Contact | Expires |
|------|--------|--------------|---------|---------|
| EMAIL_REVIEW_<slug>.md | Send email | — | new@contact.com | 2026-02-26T10:00:00Z |
| LINKEDIN_DRAFT_<slug>.md | Post to LinkedIn | — | LinkedIn | 2026-02-26T10:00:00Z |
| PAYMENT_<slug>.md | Transfer £80 | £80 | Supplier X | 2026-02-26T10:00:00Z |
```

If empty: `| — No approvals pending — | — | — | — | — |`

---

### Step 6 — Rewrite LinkedIn Queue table

```markdown
## LinkedIn Queue

| Draft File | Topic | Post Type | Created | Status |
|------------|-------|-----------|---------|--------|
| LINKEDIN_DRAFT_<slug>.md | <topic> | thought_leadership | 2026-02-25 | ⏳ Awaiting approval |
```

If empty: `| — No LinkedIn drafts — | — | — | — | — |`

---

### Step 7 — Append to Recent Activity Log

Add rows for any actions taken in this cycle (newest first):

```markdown
| <timestamp> | <action description> | ✅ Done |
```

Examples:
```
| 2026-02-25T10:30:00Z | SKILL_Gmail_Triage — 3 emails triaged (1 DRAFT, 1 ESCALATED, 1 LOG) | ✅ Done |
| 2026-02-25T10:25:00Z | GmailWatcher — captured 3 emails to Needs_Action/ | ✅ Done |
```

Keep the log to the most recent 20 entries — trim oldest if needed.

---

### Step 8 — Rewrite Daily Summary (if new content)

If this run has new information to add (new events, completed plans, significant outcomes):

```markdown
## Daily Summary

**<YYYY-MM-DD> — <narrative title>**

<2-4 sentence narrative of what happened today>

**Key outcomes:**
- <bullet point>
- <bullet point>
```

If no new content, leave the existing Daily Summary unchanged.

---

### Step 9 — Output confirmation

```
📊 Dashboard.md Updated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Timestamp:          <ISO timestamp>
  Inbox:              <N> items
  Needs Action:       <N> items
  Plans:              <N> pending
  In Progress:        <N> active
  Done today:         <N> items
  Pending Approvals:  <N> awaiting decision
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

*Silver Tier Agent Skill — always run this last after any processing cycle to keep Dashboard accurate.*
