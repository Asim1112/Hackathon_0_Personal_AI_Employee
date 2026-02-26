---
skill: daily_briefing
version: 1.0
tier: silver
trigger: scheduled (8 AM daily by scheduler.py)
inputs:
  - Dashboard.md (current state)
  - Needs_Action/ (current queue)
  - Pending_Approval/ (awaiting decisions)
  - In_Progress/ (ongoing plans)
outputs:
  - Dashboard.md Daily Summary section updated
  - Morning briefing written to Inbox/BRIEFING_<date>.md
reads:
  - Dashboard.md
  - Needs_Action/*.md
  - Pending_Approval/*.md
  - In_Progress/*.md
  - Company_Handbook.md (Section 7 — working hours)
writes:
  - Dashboard.md (Daily Summary section)
  - Inbox/BRIEFING_<YYYY-MM-DD>.md
created: 2026-02-25
---

# SKILL: Daily Briefing (Silver Tier)

## What This Skill Does

Generates the morning briefing each day at 8 AM. Reads the current state of the
vault, summarises overnight activity, flags urgent items, and writes a human-readable
briefing to `Inbox/`. Also refreshes the Dashboard.md Daily Summary section.

This is the first skill run in the daily 8 AM workflow.

---

## When to Run This Skill

Run this skill:
- At 8:00 AM daily (triggered by `orchestrator.py`)
- When the user asks for "morning briefing", "daily summary", or "what happened overnight"
- At the start of any Claude session after an absence of 4+ hours

---

## Pre-Conditions

- [ ] Read `Company_Handbook.md` Section 7 (Working Hours)
- [ ] Read `Dashboard.md` to understand yesterday's state
- [ ] Check `Needs_Action/` for overnight items
- [ ] Check `Pending_Approval/` for items still awaiting decisions
- [ ] Check `In_Progress/` for plans that need continuation

---

## Step-by-Step Instructions

### Step 1 — Count and categorise overnight items

Collect:
- Files added to `Needs_Action/` since last processing cycle (by `created` timestamp)
- Files in `Pending_Approval/` past their `expires` timestamp (overdue decisions)
- Files in `In_Progress/` that were not updated in > 24 hours (stale plans)
- Any `urgent` priority items in any folder

---

### Step 2 — Assess urgency

Determine today's urgency level:

| Condition | Urgency Level |
|---|---|
| 1+ urgent items in Needs_Action/ | 🔴 HIGH ALERT |
| 1+ overdue approvals in Pending_Approval/ | 🟡 ACTION NEEDED |
| 5+ items in Needs_Action/ | 🟡 BUSY DAY |
| All clear — routine queue | 🟢 ALL CLEAR |

---

### Step 3 — Write briefing to Inbox/

**Filename:** `Inbox/BRIEFING_<YYYY-MM-DD>.md`

**Format:**

```markdown
---
type: daily_briefing
date: <YYYY-MM-DD>
created: <ISO timestamp>
urgency: <HIGH_ALERT | ACTION_NEEDED | BUSY | ALL_CLEAR>
status: unread
---

# Morning Briefing — <Weekday>, <DD Month YYYY>

> Generated at 08:00 by Claude — Silver Tier AI Employee

---

## Status: <🔴 HIGH ALERT | 🟡 ACTION NEEDED | 🟢 ALL CLEAR>

---

## Overnight Summary

**Since last cycle (<last timestamp>):**
- <N> new items in Needs_Action/
- <N> items awaiting approval in Pending_Approval/
- <N> plans in progress
- <N> items completed yesterday

---

## Urgent Items Requiring Your Attention

<If urgency is HIGH_ALERT or ACTION_NEEDED, list specific items:>

| # | Type | File | Reason | Age |
|---|------|------|--------|-----|
| 1 | 🔴 URGENT | <filename> | <why urgent> | <age> |
| 2 | ⏰ OVERDUE | <filename> | Approval overdue by <N>h | <age> |

<If ALL_CLEAR:>
No urgent items. Queue will be processed automatically.

---

## Today's Queue

**Needs Action:** <N> items
| Priority | Count | Top item |
|----------|-------|----------|
| 🔴 Urgent | N | <filename> |
| 🟡 High | N | <filename> |
| 🟢 Medium | N | — |
| ⚪ Low | N | — |

**Pending Approvals:** <N> items waiting for your decision
**Plans In Progress:** <N> active multi-step plans

---

## Pending Approvals Requiring Decision

<List any files in Pending_Approval/ — these need your action today:>

| File | Action | Value | Created |
|------|--------|-------|---------|
| <filename> | <send email / post LinkedIn / payment> | £<amount> | <date> |

<If empty:> No pending approvals.

---

## Plans In Progress

<Summarise any In_Progress/ plans:>

| Plan | Steps Done / Total | Next Step | Blocked? |
|------|-------------------|-----------|---------|
| <plan title> | 2 / 6 | <next step> | No |

---

## Today's LinkedIn Queue

<Any LinkedIn drafts awaiting approval:>

| Draft | Topic | Scheduled | Status |
|-------|-------|-----------|--------|
| <filename> | <topic> | <date> | ⏳ Awaiting approval |

---

## Notes from Yesterday

<If Dashboard.md has a Daily Summary from yesterday, summarise it in 2-3 sentences.>

---

*To act on urgent items: open the relevant file and follow the instructions.*
*Approvals: move files from Pending_Approval/ to Approved/ or Rejected/.*
*Claude will process the full queue after this briefing.*
```

---

### Step 4 — Update Dashboard.md Daily Summary

Rewrite the `## Daily Summary` section:

```markdown
## Daily Summary

**<YYYY-MM-DD> — <Day of week> Morning Briefing**

<2-3 sentence narrative of current state>

**Queue:** <N> items to process. **Priority:** <urgency level>.
**Pending decisions:** <N> approvals awaiting human action.
**Plans active:** <N> multi-step plans in progress.
```

---

### Step 5 — Output briefing confirmation

```
☀️  Daily Briefing Generated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Date:             <YYYY-MM-DD>
  Urgency:          <level>
  Overnight items:  N
  Urgent:           N
  Pending approvals: N
  Briefing written: Inbox/BRIEFING_<date>.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proceeding to SKILL_Gmail_Triage...
```

---

*Silver Tier Agent Skill — runs daily at 8 AM via scheduler.py, generates human-readable morning briefing.*
