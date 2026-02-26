---
skill: reasoning_loop
version: 2.0
tier: silver
trigger: manual | auto (any Needs_Action item that is multi-step or complex)
inputs:
  - Needs_Action/*.md — any type with more than 2 dependent actions
  - Needs_Action/*.md — type: linkedin_opportunity (always multi-step)
  - Needs_Action/*.md — type: task or type: multi_step
  - In_Progress/*.md  — ongoing plans awaiting continuation
outputs:
  - Plans/PLAN_*.md           created with checkbox steps
  - In_Progress/PLAN_*.md     when work begins
  - Done/PLAN_*.md            when all steps are complete
  - Plan.md                   macro summary row appended
  - Dashboard.md              Plans & In Progress section updated
reads:
  - Needs_Action/*.md
  - Company_Handbook.md       (sections 4, 5, 12)
  - Dashboard.md
  - Plans/*.md                (duplicate detection)
  - In_Progress/*.md          (resume detection)
writes:
  - Plans/PLAN_*.md
  - In_Progress/PLAN_*.md
  - Done/PLAN_*.md
  - Pending_Approval/*.md     (HITL gate files)
  - Plan.md
  - Dashboard.md
created: 2026-02-25
updated: 2026-02-25
ralph_wiggum: true           # emits TASK_COMPLETE when Needs_Action/ is clear
---

# SKILL: Reasoning Loop (Silver Tier)

## What This Skill Does

When Claude encounters a complex or multi-step task in `Needs_Action/`, this skill
breaks it into a numbered, checkbox-driven plan, writes it to `Plans/`, then executes
each step sequentially — ticking boxes as it goes, pausing at HITL gates, and archiving
to `Done/` when complete.

This skill is the **reasoning backbone** of the Silver AI Employee. It ensures that
no multi-step task is processed ad-hoc: every complex item gets a written plan before
work starts, and every plan is tracked to completion.

**Silver additions over Bronze SKILL_Process_Needs_Action:**
- Sales leads (`type: linkedin_opportunity`) always enter the reasoning loop
- HITL threshold is £50 (not £500) — more plans include approval gates
- LinkedIn drafting pipeline is a first-class plan template
- Ralph Wiggum loop signal (`TASK_COMPLETE`) emitted when queue clears

---

## When to Run This Skill

Run this skill when:
- A `Needs_Action/` item has `type: task`, `type: multi_step`, or `type: linkedin_opportunity`
- Any item requires 3 or more sequential steps to resolve
- Any item involves multiple external parties (client + accountant + supplier)
- Any item spans more than one processing cycle (e.g. chase invoice over multiple days)
- Any item requires HITL approval at an intermediate step (mid-flow, not just at the end)
- An existing plan in `In_Progress/` needs continuation
- You are asked to "plan this", "break this down", or "create a plan for X"

Simple items (single email reply, single log entry, one-shot acknowledgement) do NOT
need a plan — route those directly through `SKILL_Process_Needs_Action`.

---

## Sales Lead Prioritization (Silver — Key Rule)

LinkedIn items and any notification flagged `category: business_opportunity` are
treated as HIGH priority sales leads and are **always** routed through the reasoning
loop — even if they appear simple. A connection request could become a client;
an inbox message could be a contract enquiry.

**Sales lead processing order (override standard priority queue):**

| Category                 | Plan Priority | Rationale                              |
|--------------------------|---------------|----------------------------------------|
| `business_opportunity`   | HIGH          | Active sales signal — act within 4h   |
| `inbox_message`          | HIGH          | Direct contact — may be a prospect    |
| `connection_request`     | MEDIUM        | Potential future contact               |
| `mention_or_comment`     | MEDIUM        | Engagement — respond to build presence |
| All other LinkedIn items | LOW           | Informational — log only               |

For `business_opportunity` items: the plan MUST include a LinkedIn post draft step
(`SKILL_LinkedIn_Draft`) in addition to any direct reply.

---

## Pre-Conditions (check before starting)

- [ ] Read `Company_Handbook.md` (Sections 4, 5, 12) before any plan is created
- [ ] Read `Dashboard.md` to understand current vault state and open plans
- [ ] List all files in `Needs_Action/` with `status: pending`
- [ ] List all files in `In_Progress/` that may already be handling these items
- [ ] Check `Plans/` to avoid creating duplicate plans for the same task

---

## Step 0 — Queue Inventory and Sorting

Before creating any plan, build a sorted processing list from `Needs_Action/`:

```
Reasoning Loop queue: N items
  [1] HIGH   — LINKEDIN_2026-02-25_Business_Proposal_abc123.md  (sales lead)
  [2] HIGH   — EMAIL_2026-02-25_New_Client_Enquiry_abc456.md
  [3] MEDIUM — LINKEDIN_2026-02-25_Connection_Request_def789.md
  [4] LOW    — TASK_2026-02-25_Update_Service_Listing.md
```

Items that do NOT qualify for the reasoning loop: pass directly to
`SKILL_Process_Needs_Action` (simple email replies, single-log items, etc.).

---

## Step 1 — Assess the Task

For each qualifying item, read the full file and determine:

| Question | Answer determines |
|---|---|
| What is the end goal? | Plan `goal:` field |
| What are all the steps to reach it? | Plan `## Steps` checkboxes |
| Does any step require HITL? | `## HITL Gates` section |
| Is information missing? | First step = "Gather X" |
| Is this a LinkedIn item? | Use LinkedIn Pipeline template |
| Does this involve a new contact? | Add HITL gate at send step |
| Is there a payment > £50? | Add HITL gate at payment step |

**Simple vs. complex decision:**
- **Simple** → single action, no dependencies, fully resolves in this response → skip to SKILL_Process_Needs_Action
- **Complex** → 3+ sequential steps, OR needs HITL mid-flow, OR LinkedIn item → create a plan here

---

## Step 2 — Check for Existing Plans

Before creating a new plan:

1. Search `Plans/` for any file whose `source_item:` matches the current Needs_Action filename
2. Search `In_Progress/` for any ongoing plan referencing this item

**If an existing plan is found:**
- Read it and identify the next unchecked `- [ ]` step
- Skip plan creation — jump directly to Step 4 (execute next step)
- Log: `Resuming existing plan: In_Progress/PLAN_<slug>.md at Step N`

---

## Step 3 — Create the Plan File

**Filename:** `Plans/PLAN_<slug>_<YYYY-MM-DD>.md`

Where `<slug>` is a short kebab-case description of the task (e.g. `Onboard-Apex-Ltd`,
`LinkedIn-Business-Proposal`, `Invoice-Chase-Q1-Widget-Co`).

**Template:**

```markdown
---
type: plan
source_item: "<Needs_Action filename>"
category: <email | linkedin | task | invoice | onboarding | other>
priority: <urgent | high | medium | low>
created: <ISO timestamp>
status: pending
goal: "<one sentence: what done looks like>"
estimated_steps: <N>
hitl_gates: <N>
---

# Plan: <Short Descriptive Title>

**Goal:** <What needs to be achieved — one sentence>
**Source:** `<Needs_Action filename>`
**Priority:** <priority>
**Created:** <ISO timestamp>

---

## Steps

- [ ] Step 1: <Specific, actionable step>
- [ ] Step 2: <e.g. "Write DRAFT_REPLY_Invoice_1042_2026-02-25.md to Inbox/">
- [ ] Step 3: <e.g. "Move draft to Pending_Approval/ — new contact, HITL required">
- [ ] Step 4: <e.g. "After approval, email-mcp sends reply">
- [ ] Step 5: <e.g. "Update Dashboard.md and move source file to Done/">

---

## Context & Constraints

<Any relevant context, rules, or information needed while executing this plan.
Include: contact details, amounts, deadlines, relevant Handbook sections.>

---

## HITL Gates

Steps that require human approval before proceeding:

| Step | Reason | Approval file |
|------|--------|---------------|
| Step 3 | New contact — first outbound message | Pending_Approval/EMAIL_REVIEW_<slug>.md |
| Step N | Payment £<amount> over £50 threshold | Pending_Approval/PAYMENT_<slug>.md |

*(Leave blank if no HITL gates)*

---

*Plan created by Reasoning Loop — Silver Tier AI Employee*
```

---

## Step 4 — Execute the Plan

Once a plan exists (new or resumed):

1. Move the file: `Plans/PLAN_<slug>.md` → `In_Progress/PLAN_<slug>.md`
2. Update frontmatter: `status: pending` → `status: in_progress`
3. Execute steps **sequentially top-to-bottom** — never skip ahead
4. After each completed step, tick the checkbox and add a completion note:

```markdown
- [x] Step 1: Draft reply email to client@example.com re: Invoice #1042
  > Completed 2026-02-25T10:05:00Z — DRAFT_REPLY_Invoice_1042_2026-02-25.md written to Inbox/
```

5. Record any output files created (draft filenames, approval filenames, etc.)
6. If a step creates another file, note it under the checkbox

---

## Step 5 — Handle HITL Gates

When a step requires human approval (new contact, payment > £50, LinkedIn post, email via MCP):

**5a. Write the approval file to `Pending_Approval/`** using the format from `SKILL_Process_Needs_Action`.

**5b. Mark the step as blocked in the plan:**

```markdown
- [~] Step 3: Move draft to Pending_Approval/ — HITL required (new contact)
  > ⏳ WAITING — EMAIL_REVIEW_Welcome_Apex_2026-02-25.md written to Pending_Approval/
  > Waiting for human to move to /Approved/ or /Rejected/
```

**5c. Update `Dashboard.md` Pending Approvals table.**

**5d. STOP** — do not execute steps beyond a `[~]` gate until approval is received.

**5e. On resumption**, check `Approved/` or `Rejected/`:
- File in `Approved/` → tick `[~]` to `[x]`, continue to next step
- File in `Rejected/` → note rejection, decide whether to cancel plan or take alternative path

---

## Step 6 — Complete the Plan

When ALL steps are `- [x]` (no pending `- [ ]` or blocked `- [~]`):

1. Update frontmatter: `status: in_progress` → `status: complete`, add `completed_at: <timestamp>`
2. Append the completion summary:

```markdown
---

## Completion Summary

**Completed:** <ISO timestamp>
**Total steps:** <N>
**Steps completed:** <N>
**Steps skipped:** <N> *(explain any skipped steps)*
**Outcome:** <2-3 sentences: what was achieved, what was sent/created/logged>
**Files created:**
  - Inbox/DRAFT_REPLY_<slug>.md
  - Pending_Approval/EMAIL_REVIEW_<slug>.md → Approved/
  - Done/<source_item_filename>.md
```

3. Move file: `In_Progress/PLAN_<slug>.md` → `Done/PLAN_<slug>.md`
4. Move source `Needs_Action/` item to `Done/` with `status: processed` and `processed_at: <timestamp>`.

---

## Step 7 — Update Plan.md and Dashboard.md

**Append to `Plan.md`** (macro progress tracker) under "Completed Tasks":

```
| 2026-02-25 | Plan: <title> | ✅ Complete | <N> steps | <one-line outcome> |
```

**Update `Dashboard.md`:**
- Remove completed plan from Plans & In Progress table
- Add row to Recent Activity Log:
  ```
  | <timestamp> | Completed PLAN_<slug>.md — <outcome summary> | ✅ Done |
  ```
- Recount: Items in Plans, Items In_Progress, Items Done Today, Pending Approvals

---

## Step 8 — Ralph Wiggum Loop Signal

After processing all plans and returning all qualifying `Needs_Action/` items to `Done/`:

1. Count remaining `.md` files in `Needs_Action/` with `status: pending`
2. If count is **zero** → write `TASK_COMPLETE` as the last line of the response
3. If count is **non-zero** → list the remaining files, continue processing

The Ralph Wiggum stop hook (`stop_hook.py`) reads `TASK_COMPLETE` to know the loop
can exit. If Needs_Action/ is still non-empty, the hook re-injects the prompt and
Claude continues in the next iteration (up to `max_iterations` in `.ralph_state.json`).

**Do NOT write `TASK_COMPLETE` if any file remains in `Needs_Action/` with `status: pending`.**

---

## Multi-step Task Templates

Use these prefab step sequences for common Silver-tier task types.
Adapt as needed — add or remove steps based on the specific item.

### Template A — Email Thread Reply (Existing Contact)

```
- [ ] Step 1: Read email item fully and classify intent (query / complaint / invoice / general)
- [ ] Step 2: Draft reply in Inbox/DRAFT_REPLY_<slug>_<date>.md
- [ ] Step 3: Review against Company_Handbook tone rules
- [ ] Step 4: Move draft to Pending_Approval/ (email-mcp sends after /Approved/)
- [ ] Step 5: Log in Dashboard.md and move source to Done/
```

### Template B — LinkedIn Business Opportunity Pipeline

```
- [ ] Step 1: Read opportunity notification and classify (proposal / DM / mention)
- [ ] Step 2: Research sender if possible (public LinkedIn profile, prior interactions)
- [ ] Step 3: Draft a direct reply (if DM) → Pending_Approval/ (HITL — outbound contact)
- [ ] Step 4: Run SKILL_LinkedIn_Draft → create promotional post → Pending_Approval/
- [ ] Step 5: Log opportunity as business intelligence in Dashboard.md
- [ ] Step 6: Move source item to Done/ with full processing notes
```

### Template C — Invoice Chase

```
- [ ] Step 1: Confirm invoice details (amount, due date, counterparty) from source file
- [ ] Step 2: Check if overdue (>3 days past due date per Handbook Section 2)
- [ ] Step 3: Draft polite reminder email → Inbox/DRAFT_REPLY_InvoiceChase_<slug>_<date>.md
- [ ] Step 4: Move to Pending_Approval/ (email-mcp sends on /Approved/)
- [ ] Step 5: Log in Dashboard.md Expense tracking section
- [ ] Step 6: Move source to Done/
```

### Template D — New Client Onboarding

```
- [ ] Step 1: Capture client details from source item (name, email, project scope)
- [ ] Step 2: Create client contact record → Needs_Action/ or a dedicated contacts file
- [ ] Step 3: Draft welcome email → Inbox/DRAFT_REPLY_Welcome_<slug>_<date>.md
- [ ] Step 4: Move to Pending_Approval/ — new contact rule (HITL required)
- [ ] Step 5: Draft invoice template for first engagement → Needs_Action/
- [ ] Step 6: Log onboarding in Dashboard.md and move source to Done/
```

### Template E — Payment Approval (>£50)

```
- [ ] Step 1: Confirm payment details (recipient, amount, purpose, reference)
- [ ] Step 2: Cross-check against pre-approved recurring payments in Handbook Section 2
- [ ] Step 3: Write PAYMENT_REVIEW_<Recipient>_<date>.md to Pending_Approval/
- [ ] Step 4: Log in Dashboard.md Pending Approvals — do NOT proceed until /Approved/
- [ ] Step 5: On approval, log payment in Dashboard.md expense tracker
- [ ] Step 6: Move source to Done/
```

---

## Plan Status Reference

| Status       | Location      | Checkbox state | Meaning                              |
|--------------|---------------|----------------|--------------------------------------|
| `pending`    | `Plans/`      | All `- [ ]`    | Plan written, not yet started        |
| `in_progress`| `In_Progress/`| Mixed          | Actively executing steps             |
| `blocked`    | `In_Progress/`| Has `- [~]`    | Paused — waiting on HITL approval    |
| `complete`   | `Done/`       | All `- [x]`    | All steps executed                   |
| `cancelled`  | `Done/`       | N/A            | Abandoned — reason noted in file     |

**Step checkbox states:**
- `- [ ]` Pending — not yet started
- `- [~]` Blocked — waiting on HITL approval or external dependency
- `- [x]` Complete — executed and verified

---

## Full Example: LinkedIn Business Opportunity Plan

```markdown
---
type: plan
source_item: "LINKEDIN_2026-02-25_Business_Opportunity_consulting_a3f8b2c1.md"
category: linkedin
priority: high
created: 2026-02-25T09:00:00Z
status: in_progress
goal: "Respond to consulting enquiry and draft a LinkedIn post about the opportunity"
estimated_steps: 6
hitl_gates: 2
---

# Plan: LinkedIn Consulting Enquiry — Feb 25

**Goal:** Respond to DM about consulting engagement and publish a related LinkedIn post
**Source:** `LINKEDIN_2026-02-25_Business_Opportunity_consulting_a3f8b2c1.md`
**Priority:** High (sales lead — business_opportunity category)
**Created:** 2026-02-25T09:00:00Z

---

## Steps

- [x] Step 1: Read opportunity notification — classified as consulting DM from new contact
  > Completed 2026-02-25T09:05:00Z — Sender: Jane Smith, interested in AI Employee setup

- [x] Step 2: Draft direct reply to Jane Smith's DM
  > Completed 2026-02-25T09:10:00Z — DRAFT_REPLY_LinkedIn_JaneSmith_2026-02-25.md written to Inbox/

- [~] Step 3: Move DM reply to Pending_Approval/ — new contact, HITL required
  > ⏳ WAITING — EMAIL_REVIEW_LinkedIn_JaneSmith_2026-02-25.md written to Pending_Approval/
  > Waiting for /Approved/ or /Rejected/ decision

- [ ] Step 4: Run SKILL_LinkedIn_Draft — write a thought leadership post on AI Employee setup
- [ ] Step 5: Verify post meets Section 12 rules (no client name, 150-300 words, 3-5 hashtags)
- [ ] Step 6: Log opportunity in Dashboard.md and move source to Done/

---

## Context & Constraints

- Jane Smith is a NEW contact — first outbound message requires HITL (Handbook Section 4)
- LinkedIn post must NOT name Jane Smith or reference the specific enquiry
- Post quota: check Dashboard.md LinkedIn Queue before queuing the post (max 1/day, 3/week)
- Reply tone: warm, professional, solution-oriented (Handbook Section 1)

---

## HITL Gates

| Step | Reason | Approval file |
|------|--------|---------------|
| Step 3 | New contact — first outbound LinkedIn DM | Pending_Approval/EMAIL_REVIEW_LinkedIn_JaneSmith_2026-02-25.md |
| Step 4 | LinkedIn post — ALL posts require HITL approval | Pending_Approval/LINKEDIN_DRAFT_AI_Employee_Setup_2026-02-25.md |

---

*Plan created by Reasoning Loop — Silver Tier AI Employee*
```

---

## Rules Checklist (verify before marking plan complete)

- [ ] No payment over **£50** acted on without HITL approval
- [ ] No first message to a **new contact** sent without HITL approval
- [ ] No **LinkedIn post** published — draft only, in Pending_Approval/
- [ ] No email sent via MCP without file in /Approved/
- [ ] No legal/complaint item handled autonomously
- [ ] Every plan step has a completion note or a `[~]` blocked note
- [ ] `Plan.md` has a new summary row for this completed plan
- [ ] `Dashboard.md` reflects current Plans/ and In_Progress/ counts
- [ ] Source `Needs_Action/` file moved to `Done/` with `status: processed`
- [ ] `TASK_COMPLETE` written on last line **only if** Needs_Action/ is fully empty

---

*Silver Tier Agent Skill v2.0 — Reasoning loop with Plans/, HITL gates, Ralph Wiggum integration, and sales lead prioritization.*
