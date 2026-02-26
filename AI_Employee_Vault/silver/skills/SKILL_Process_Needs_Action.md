---
skill: process_needs_action
version: 2.0
tier: silver
trigger: manual | scheduled (8 AM daily, after triage)
inputs:
  - Needs_Action/ folder (one or more .md files with status: pending)
outputs:
  - Updated .md files moved to Done/
  - Complex tasks → Plans/ (via SKILL_Reasoning_Loop)
  - Dashboard.md updated (queue counts, activity log)
  - Pending_Approval/ files created for sensitive items
reads:
  - Needs_Action/*.md
  - Company_Handbook.md
  - Dashboard.md
writes:
  - Done/*.md
  - Plans/*.md (for complex tasks)
  - Dashboard.md
  - Pending_Approval/*.md (conditional)
created: 2026-02-25
---

# SKILL: Process Needs Action Queue (Silver Tier)

## What This Skill Does

Scans the `Needs_Action/` folder, processes every pending item top-to-bottom by
priority, routes complex tasks to the reasoning loop (Plans/), writes summaries
and action records into each file, moves them to `Done/`, and updates `Dashboard.md`.

**Silver changes from Bronze:**
- HITL threshold is £50 (not £500)
- Any send to a new contact → `Pending_Approval/` first
- Complex multi-step tasks → `SKILL_Reasoning_Loop` → `Plans/`
- LinkedIn items → `SKILL_LinkedIn_Draft` → `Pending_Approval/`
- MCP servers handle actual sends (not Claude)

This is the core **Reasoning → Action** loop of the Silver AI Employee.

---

## When to Run This Skill

Run this skill when:
- The watcher has deposited new `.md` files into `Needs_Action/`
- The Dashboard shows a non-zero "Items Needs Action" count
- You are asked to "process the queue", "work through inbox", or "handle pending items"
- As part of the daily 8 AM scheduled workflow

---

## Pre-Conditions (check before starting)

- [ ] Read `Company_Handbook.md` fully before processing any file
- [ ] Read current `Dashboard.md` to understand existing state
- [ ] Confirm `Needs_Action/` contains at least one file with `status: pending`
- [ ] Run `SKILL_Gmail_Triage` first if any email items are present
- [ ] Check `In_Progress/` for any ongoing plans that need continuation

---

## Step-by-Step Instructions

### Step 1 — Inventory the queue

List all files in `Needs_Action/` where frontmatter `status: pending`.
Build a priority-ordered processing list:

| Priority value | Process order |
|----------------|---------------|
| `urgent`       | 1st           |
| `high`         | 2nd           |
| `medium`       | 3rd           |
| `low`          | 4th           |

Within same priority, oldest first (by `received` or `created` timestamp).

Log the inventory:
```
Processing queue: N items
  [1] URGENT — <filename>
  [2] HIGH   — <filename>
  ...
```

---

### Step 2 — For each file, determine its type and routing

Read the file's YAML frontmatter `type` field and route accordingly:

| type value            | Skill / Handling                                              |
|-----------------------|---------------------------------------------------------------|
| `email`               | Run SKILL_Gmail_Triage first, then process here              |
| `whatsapp`            | Run SKILL_WhatsApp_Triage first, then process here           |
| `linkedin_opportunity`| Run SKILL_LinkedIn_Draft → writes to Pending_Approval/       |
| `task` (simple)       | Process directly — log + move to Done/                       |
| `task` (complex)      | Run SKILL_Reasoning_Loop → writes to Plans/                  |
| `file_drop`           | Summarise file, log to activity, move to Done/               |
| `approval_request`    | Check /Approved or /Rejected folder for decision             |
| `human_review`        | Do NOT process — flag in Dashboard, skip                     |
| *(unknown)*           | Treat as `human_review`                                      |

**How to distinguish simple vs complex tasks:**
- Simple: single action, no dependencies, completes in this response
- Complex: 3+ sequential steps, multiple parties, or requires HITL mid-flow → use Reasoning Loop

---

### Step 3 — Process each file

For every file (except `human_review` — skip those):

**3a. Read and understand the full content.**

**3b. Apply Silver HITL rules (check before doing anything):**
- Payment over **£50** → do NOT act → write to `Pending_Approval/`
- Send to **new contact** → do NOT send → write to `Pending_Approval/`
- **LinkedIn post** → do NOT post → run SKILL_LinkedIn_Draft
- Legal/complaint keywords → write to `Pending_Approval/` as HUMAN_REVIEW
- When in doubt → escalate, never guess

**3c. Write analysis into the file's `## Processing Notes` section:**

```markdown
## Processing Notes

**Processed:** 2026-02-25T10:00:00Z
**Claude Analysis:** <2-4 sentence summary of what this item is and why it matters>
**Action Taken:** <what was done — draft written / plan created / escalated / logged>
**Outcome:** <result — e.g. "Plan created at Plans/PLAN_Onboard_Apex_2026-02-25.md" or "Moved to Pending_Approval/">
**HITL triggered:** <Yes — reason | No>
```

**3d. Update the file's frontmatter `status` field:**
- Change `status: pending` → `status: processed`
- Add `processed_at: <ISO timestamp>`

**3e. Move the file from `Needs_Action/` to `Done/`.**

Keep the original filename. If duplicate exists in Done/, append `_v2`, `_v3`, etc.

---

### Step 4 — Update Dashboard.md

After processing all files, rewrite relevant sections:

**System Status table:**
```markdown
| Last Updated           | <current ISO timestamp>          |
| Items in Inbox         | <count files in Inbox/>          |
| Items Needs Action     | <count remaining pending>        |
| Items in Plans         | <count files in Plans/>          |
| Items In_Progress      | <count files in In_Progress/>    |
| Items Done Today       | <count moved today>              |
| Pending Approvals      | <count in Pending_Approval/>     |
```

**Needs Action Queue table** (reflect remaining or show empty):
```markdown
| File | Type | Priority | Age |
|------|------|----------|-----|
| — Queue is empty — | — | — | — |
```

**Plans & In Progress table** (reflect any new plans):
```markdown
| File | Goal | Status | Steps Done | Steps Total |
|------|------|--------|------------|-------------|
| PLAN_<slug>.md | <goal> | in_progress | 2 | 6 |
```

**Recent Activity Log** (append newest first):
```markdown
| <timestamp> | Processed <filename> — <one-line summary> | ✅ Done |
```

**Pending Approvals table** if new files written to `Pending_Approval/`:
```markdown
| FILE_REVIEW_<slug>.md | <action> | £<amount> | <contact> | <expiry> |
```

---

### Step 5 — Final confirmation

```
✅ Processed N items from Needs_Action/ (Silver Tier)
   → N moved to Done/
   → N → Plans/ (complex tasks, reasoning loop)
   → N → Pending_Approval/ (HITL required)
   → N skipped (human_review)
   → N LinkedIn drafts created (Pending_Approval/)
Dashboard.md updated.
```

---

## Rules Checklist (from Company_Handbook.md)

Before marking any item as processed, confirm:

- [ ] No payment over **£50** was acted on directly
- [ ] No send to a **new contact** happened without HITL
- [ ] No LinkedIn post was published without HITL approval
- [ ] No legal/complaint item was handled autonomously
- [ ] No external communication was sent (MCP sends after /Approved/ only)
- [ ] `Dashboard.md` reflects the current true state
- [ ] Every processed file has a `## Processing Notes` entry
- [ ] Complex tasks have a corresponding plan in `Plans/`

---

## Output File Format (Done/)

Every file moved to `Done/` must have this structure:

```markdown
---
type: <original type>
...original frontmatter fields...
status: processed
processed_at: 2026-02-25T10:00:00Z
---

<original content unchanged>

---

## Processing Notes

**Processed:** 2026-02-25T10:00:00Z
**Claude Analysis:** ...
**Action Taken:** ...
**Outcome:** ...
**HITL triggered:** ...
```

---

## Pending Approval File Format

When a sensitive item requires human sign-off:

```markdown
---
type: approval_request
source_file: <original filename>
action: <what action is being requested>
reason: <why this needs approval — e.g. "Payment over £50" or "New contact">
amount: <£ amount if financial>
contact: <email/name if new contact>
created: <ISO timestamp>
expires: <ISO timestamp — 24h from created>
status: pending
send_via_mcp: <email-mcp | linkedin-mcp | none>
---

## What Happened

<Brief description of the original item>

## Requested Action

<What Claude would do if approved>

## HITL Trigger

<Which Silver tier rule triggered this escalation>

## To Approve

Move this file to /Approved/ folder.
The relevant MCP server will execute the action automatically.

## To Reject

Move this file to /Rejected/ folder.
```

---

*Silver Tier Agent Skill — HITL-first, MCP-enabled, reasoning loop integrated.*
