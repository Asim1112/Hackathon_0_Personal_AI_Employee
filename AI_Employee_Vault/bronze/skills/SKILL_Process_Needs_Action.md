---
skill: process_needs_action
version: 1.0
trigger: manual
inputs:
  - Needs_Action/ folder (one or more .md files with status: pending)
outputs:
  - Updated .md files moved to Done/
  - Dashboard.md updated (queue counts, activity log)
  - Pending_Approval/ files created for sensitive items
reads:
  - Needs_Action/*.md
  - Company_Handbook.md
  - Dashboard.md
writes:
  - Done/*.md
  - Dashboard.md
  - Pending_Approval/*.md (conditional)
created: 2026-02-24
---

# SKILL: Process Needs Action Queue

## What This Skill Does

Scans the `Needs_Action/` folder, processes every pending item top-to-bottom by
priority, writes a summary and action record into each file, moves it to `Done/`,
and updates `Dashboard.md` to reflect the new state.

This is the core "Reasoning → Action" loop of the Bronze AI Employee.

---

## When to Run This Skill

Run this skill when:
- The watcher has deposited new `.md` files into `Needs_Action/`
- The Dashboard shows a non-zero "Items Needs Action" count
- You are asked to "process the queue", "work through inbox", or "handle pending items"

---

## Pre-Conditions (check before starting)

- [ ] Read `Company_Handbook.md` fully before processing any file
- [ ] Read current `Dashboard.md` to understand existing state
- [ ] Confirm `Needs_Action/` contains at least one file with `status: pending`

---

## Step-by-Step Instructions

### Step 1 — Inventory the queue

List all files in `Needs_Action/` where frontmatter `status: pending`.
Build a priority-ordered processing list using this sort order:

| Priority value | Process order |
|----------------|---------------|
| `urgent`       | 1st           |
| `high`         | 2nd           |
| `medium`       | 3rd           |
| `low`          | 4th           |

If two files share the same priority, process the older one first (by `received` timestamp).

Log the inventory as:
```
Processing queue: N items
  [1] URGENT — <filename>
  [2] HIGH   — <filename>
  ...
```

---

### Step 2 — For each file, determine its type

Read the file's YAML frontmatter `type` field and route accordingly:

| type value     | Handling skill to apply              |
|----------------|--------------------------------------|
| `email`        | Run SKILL_Gmail_Triage.md            |
| `file_drop`    | Summarise file, log to activity      |
| `approval_request` | Check /Approved or /Rejected folder |
| `human_review` | Do NOT process — flag in Dashboard   |
| *(unknown)*    | Treat as `human_review`              |

---

### Step 3 — Process each file

For every file (except `human_review` — skip those):

**3a. Read and understand the full content.**

**3b. Write your analysis into the file's `## Processing Notes` section:**

```markdown
## Processing Notes

**Processed:** 2026-02-24T10:00:00Z
**Claude Analysis:** <2-4 sentence summary of what this item is and why it matters>
**Action Taken:** <what was done — draft written / flagged / logged / no action needed>
**Outcome:** <result — e.g. "Draft reply saved to Inbox/" or "Moved to Pending_Approval/">
```

**3c. Update the file's frontmatter `status` field:**
- Change `status: pending` → `status: processed`
- Add `processed_at: <ISO timestamp>`

**3d. Apply Company_Handbook rules** (always):
- Payment over threshold → do NOT act → write to `Pending_Approval/` instead
- Legal/complaint keywords → write to `Pending_Approval/` as HUMAN_REVIEW
- Communication responses → draft only, never send directly (Bronze tier)
- When in doubt → escalate to `Pending_Approval/`, never guess

**3e. Move the file from `Needs_Action/` to `Done/`.**

File naming in Done/:
- Keep the original filename exactly
- If a file with that name already exists in Done/, append `_v2`, `_v3`, etc.

---

### Step 4 — Update Dashboard.md

After processing all files, rewrite the relevant sections of `Dashboard.md`:

**Update the System Status table:**
```markdown
| Last Updated       | <current ISO timestamp>     |
| Items in Inbox     | <count files in Inbox/>     |
| Items Needs Action | <count remaining pending>   |
| Items Done Today   | <count moved today>         |
```

**Update the Needs Action Queue table** (reflect remaining items or show empty):
```markdown
| File | Type | Priority | Age |
|------|------|----------|-----|
| — Queue is empty — | — | — | — |
```

**Append rows to the Recent Activity Log** (newest first, one row per processed file):
```markdown
| <timestamp> | Processed <filename> — <one-line summary> | ✅ Done |
```

**Update Pending Approvals table** if any new files were written to `Pending_Approval/`.

---

### Step 5 — Final confirmation

Output a plain-language summary of what was done:

```
✅ Processed N items from Needs_Action/
   → N moved to Done/
   → N flagged to Pending_Approval/
   → N skipped (human_review)
Dashboard.md updated.
```

---

## Rules Checklist (from Company_Handbook.md)

Before marking any item as processed, confirm:

- [ ] No payment over threshold was acted on directly
- [ ] No external communication was sent (drafts only in Bronze)
- [ ] No legal/complaint item was handled autonomously
- [ ] `Dashboard.md` reflects the current true state
- [ ] Every processed file has a `## Processing Notes` entry

---

## Output File Format (Done/)

Every file moved to `Done/` must have this structure before moving:

```markdown
---
type: <original type>
...original frontmatter fields...
status: processed
processed_at: 2026-02-24T10:00:00Z
---

<original content unchanged above this line>

---

## Processing Notes

**Processed:** 2026-02-24T10:00:00Z
**Claude Analysis:** ...
**Action Taken:** ...
**Outcome:** ...
```

---

## Pending Approval File Format

When a sensitive item requires human sign-off, write this to `Pending_Approval/`:

```markdown
---
type: approval_request
source_file: <original filename in Done/>
action: <what action is being requested>
reason: <why this needs approval>
created: <ISO timestamp>
expires: <ISO timestamp — 24h from created>
status: pending
---

## What Happened

<Brief description of the original item>

## Requested Action

<What Claude would do if approved>

## To Approve

Move this file to /Approved folder.

## To Reject

Move this file to /Rejected folder.
```

---

## Usage Examples

### Example 1 — Run via Claude prompt

```
Use SKILL_Process_Needs_Action to process all pending items in the queue.
```

### Example 2 — Targeted run

```
Use SKILL_Process_Needs_Action on Needs_Action/EMAIL_2026-02-24_Invoice_abc123.md only.
```

### Example 3 — Combined with triage

```
Use SKILL_Gmail_Triage to triage all emails, then use SKILL_Process_Needs_Action
to process everything that isn't flagged for human review.
```

---

*Bronze Tier Agent Skill — reads/writes vault only, no external actions.*
