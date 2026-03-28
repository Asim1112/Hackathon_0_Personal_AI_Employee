---
skill: hitl_approval
version: 1.0
tier: silver
trigger: called by other skills — never invoked directly by a user prompt alone
inputs:
  - Any action that requires human authorisation before execution
outputs:
  - Pending_Approval/<TYPE>_REVIEW_<slug>_<date>.md  written with status: pending
  - In_Progress/PLAN_*.md  updated with [~] blocked step (when inside a reasoning loop)
  - Dashboard.md  Pending Approvals table updated
reads:
  - Company_Handbook.md  Section 4 (HITL trigger list)
  - Dashboard.md         (current approval queue + LinkedIn post quota)
  - In_Progress/PLAN_*.md  (if HITL is mid-plan — to mark step blocked)
writes:
  - Pending_Approval/*.md
  - In_Progress/PLAN_*.md  (blocked step notation)
  - Dashboard.md
called_by:
  - SKILL_Gmail_Triage     (new contact / payment > £50 / legal keywords)
  - SKILL_LinkedIn_Draft   (all LinkedIn posts, always)
  - SKILL_Reasoning_Loop   (mid-plan steps that hit a HITL gate)
  - SKILL_Process_Needs_Action  (any item that cannot be acted on autonomously)
triggers_mcp:
  - email-mcp      (watches Approved/ for type: draft_reply)
  - linkedin-mcp   (watches Approved/ for type: linkedin_draft)
created: 2026-02-25
---

# SKILL: HITL Approval (Silver Tier)

> ⚠️ **CRITICAL — Do NOT use this skill to write social media drafts or Odoo action files.**
>
> This skill writes `type: approval_request` files — these are **human-review-only** files that do NOT trigger any MCP server.
>
> For files that WILL be acted on by an MCP after approval, use the platform-specific skill instead:
> - Twitter posts → use **SKILL_Twitter_Draft** (writes `type: social_draft` + `send_via_mcp: twitter-mcp`)
> - Facebook/Instagram posts → use **SKILL_Facebook_Instagram** (writes `type: social_post` + `send_via_mcp: facebook-instagram-mcp`)
> - LinkedIn posts → use **SKILL_LinkedIn_Draft** (writes `type: linkedin_draft` + `send_via_mcp: linkedin-mcp`)
> - Odoo invoices → use **SKILL_Odoo_Accounting** (writes `type: odoo_action` + `send_via_mcp: odoo-mcp`)
> - Email replies → use **SKILL_Gmail_Triage** (writes `type: draft_reply` + `send_via_mcp: email-mcp`)
>
> Use THIS skill only for: new contact reviews, payment approvals, legal/compliance reviews, and other decisions that require human judgement but do NOT directly trigger an MCP server.

## What This Skill Does

Provides the canonical **Human-in-the-Loop gate** for the Silver AI Employee.

Whenever Claude must take an action that is irreversible, external, financial, or
carries reputational risk, this skill:

1. Writes a structured `.md` file to `Pending_Approval/` — never acts directly
2. Marks any parent plan step as `[~]` (blocked) in `In_Progress/`
3. Updates the Dashboard Pending Approvals table
4. Stops — the human decides by moving the file to `/Approved/` or `/Rejected/`
5. The relevant MCP server fires automatically on `/Approved/` (no Claude involvement)

**Claude is never the sender. Claude is never the poster. The MCP servers are.**

---

## HITL Trigger Table

Invoke this skill whenever ANY of the following conditions are true.
These mirror Company_Handbook.md Section 4 exactly.

| # | Trigger | Subtype | MCP that executes |
|---|---------|---------|-------------------|
| 1 | Any email sent via MCP | `email_send` | `email-mcp` |
| 2 | First message to a new contact (any channel) | `new_contact` | `email-mcp` or `linkedin-mcp` |
| 3 | Any LinkedIn post, regardless of content | `linkedin_post` | `linkedin-mcp` |
| 4 | Any payment or transfer over **£50** | `payment` | `none` (human action) |
| 5 | Signing or agreeing to a contract or legal document | `legal_agreement` | `none` |
| 6 | Sharing private or confidential data with a third party | `data_share` | `none` |
| 7 | Deleting or archiving client records | `data_deletion` | `none` |
| 8 | Responding to a formal complaint or legal notice | `complaint_response` | `email-mcp` |
| 9 | Onboarding or offboarding a team member | `hr_action` | `none` |
| 10 | Any action not explicitly covered in Company_Handbook.md | `unclassified` | `none` |

If in doubt: **default to HITL**. It is always safer to write a file than to act.

---

## Step 1 — Write the Pending_Approval File

### Filename convention

```
Pending_Approval/<SUBTYPE>_REVIEW_<slug>_<YYYY-MM-DD>.md
```

Examples:
- `EMAIL_REVIEW_Invoice_Query_2026-02-25.md`
- `LINKEDIN_DRAFT_AI_Employee_Launch_2026-02-25.md`
- `PAYMENT_REVIEW_Supplier_X_2026-02-25.md`
- `NEW_CONTACT_REVIEW_Jane_Smith_2026-02-25.md`

### Universal YAML frontmatter (all approval types)

```yaml
---
type: approval_request
subtype: <email_send | linkedin_post | payment | new_contact | legal_agreement | data_share | data_deletion | complaint_response | hr_action | unclassified>
source_file: "<originating Needs_Action or Inbox filename>"
source_skill: "<SKILL_Gmail_Triage | SKILL_LinkedIn_Draft | SKILL_Reasoning_Loop | ...>"
plan_ref: "<In_Progress/PLAN_*.md filename if mid-plan, else blank>"
action: "<single sentence: what Claude is requesting permission to do>"
priority: <urgent | high | medium | low>
created: "<ISO timestamp>"
expires: "<ISO timestamp — 24 hours after created>"
status: pending
mcp_trigger: <email-mcp | linkedin-mcp | none>
---
```

### Action-type additional fields

Append these fields inside the YAML block depending on subtype:

**email_send / new_contact (email channel):**
```yaml
to: "<recipient email>"
subject: "<email subject line>"
draft_file: "<Inbox/DRAFT_REPLY_*.md>"
```

**linkedin_post:**
```yaml
post_type: <success_story | service_announcement | thought_leadership | celebration>
word_count: <N>
scheduled_for: "<YYYY-MM-DD or ASAP>"
draft_file: "<Pending_Approval/LINKEDIN_DRAFT_*.md>"
```

**payment:**
```yaml
amount: "<£ figure>"
recipient: "<payee name>"
reference: "<invoice or PO reference>"
account_last4: "<XXXX — never full account number>"
```

### Markdown body (follows the YAML block)

```markdown
# Approval Request: <Short action description>

> **Action required:** Move this file to `/Approved/` to proceed, or `/Rejected/` to cancel.
> Expires: <expiry timestamp>

---

## What Happened

<1–2 sentences: the original item and why this action is needed>

## Requested Action

<Exactly what will happen if approved — be specific: who receives what, when, via which channel>

## Why HITL Is Required

**Rule triggered:** Company_Handbook.md Section 4, trigger #<N>
**Reason:** <e.g. "New contact — first outbound message" or "LinkedIn post requires approval" or "Payment of £80 exceeds £50 threshold">

## Relevant Context

<Any business context Claude has: sender background, previous correspondence, amount breakdown, LinkedIn post word count, hashtags, etc.>

## Options

- **Approve:** Move file to `/Approved/` — MCP server executes automatically
- **Reject:** Move file to `/Rejected/` — no action taken, source file logged
- **Edit first:** Amend the draft file listed in `draft_file:`, then move this to `/Approved/`

---

*Written by <source_skill> — Silver Tier AI Employee*
```

---

## Step 2 — Mark Reasoning Loop Step as Blocked

If this HITL call happens inside an active plan in `In_Progress/`:

1. Open the plan file (`plan_ref:` field above)
2. Find the current step and change it from `- [ ]` to `- [~]`:

```markdown
- [~] Step 3: Move draft to Pending_Approval/ — new contact, HITL required
  > ⏳ WAITING — EMAIL_REVIEW_Jane_Smith_2026-02-25.md written to Pending_Approval/
  > Plan paused. Resume after human decision in /Approved/ or /Rejected/.
```

3. Update plan frontmatter: `status: in_progress` → `status: blocked`
4. **Do not execute any further steps** in the plan until the HITL resolves

---

## Step 3 — Update Dashboard

After writing the Pending_Approval file, add a row to the `## Pending Approvals` table in `Dashboard.md`:

```markdown
| <filename> | <action one-liner> | <£amount or —> | <contact or channel> | <expiry> |
```

Example rows:
```
| EMAIL_REVIEW_Jane_Smith_2026-02-25.md | Send welcome email | — | jane@example.com | 2026-02-26T10:00Z |
| LINKEDIN_DRAFT_AI_Launch_2026-02-25.md | Post to LinkedIn | — | LinkedIn | 2026-02-26T10:00Z |
| PAYMENT_REVIEW_Supplier_X_2026-02-25.md | Transfer to Supplier X | £120 | Supplier X | 2026-02-26T10:00Z |
```

---

## Orchestrator Pattern — How Approvals Execute

Claude does **not** call MCP servers. The MCP servers are always-on processes that
watch the vault filesystem and fire when a human moves a file to `/Approved/`.

```
Claude writes  →  Pending_Approval/<file>.md  (status: pending)
                         ↓
        Human reads draft, decides to approve
                         ↓
        Human moves file  →  Approved/<file>.md
                         ↓
 chokidar 'add' event  →  email-mcp  OR  linkedin-mcp  fires
                         ↓
       MCP reads file, executes action (send email / post to LinkedIn)
                         ↓
       MCP writes result  →  Done/<file>.md  (status: sent / posted)
```

**MCP routing** is determined by the `mcp_trigger:` field in the YAML:
- `email-mcp` → sends the email draft referenced in `draft_file:`
- `linkedin-mcp` → posts the LinkedIn draft referenced in `draft_file:`
- `none` → human executes the action manually; MCP only logs the approval

---

## On Approval — Claude's Resumption Steps

When a file moves from `Pending_Approval/` → `Approved/`:

1. The MCP server handles the actual send/post (Claude does not need to act for `email-mcp` / `linkedin-mcp`)
2. For `mcp_trigger: none` (payment, legal, HR): Claude must be re-invoked to continue
3. When Claude resumes the parent plan:
   - Change `- [~]` → `- [x]` on the previously blocked step
   - Add completion note: `> Approved <timestamp> — MCP sent / human executed`
   - Update plan `status: blocked` → `status: in_progress`
   - Continue to the next `- [ ]` step

---

## On Rejection — Claude's Rejection Steps

When a file moves from `Pending_Approval/` → `Rejected/`:

1. Open the parent plan (if any) — find the `- [~]` blocked step
2. Change `- [~]` → `- [x]` and note the rejection:
   ```
   - [x] Step 3: Move draft to Pending_Approval/
     > ❌ REJECTED <timestamp> — Human declined. No action taken.
   ```
3. Decide next steps based on context:
   - If there is a viable alternative path → create a new step `- [ ]` for it
   - If the plan cannot continue without this action → mark plan `status: cancelled`, note reason
4. Update `Dashboard.md`: remove from Pending Approvals, add to Recent Activity Log
5. Move the source `Needs_Action/` file to `Done/` with `status: rejected`

---

## Skill Integration Map

```
SKILL_Gmail_Triage
  → trigger #2 (new contact) or #4 (payment > £50) or #8 (complaint)
  → calls SKILL_HITL_Approval → writes EMAIL_REVIEW_*.md

SKILL_LinkedIn_Draft
  → trigger #3 (all LinkedIn posts, always)
  → calls SKILL_HITL_Approval → writes LINKEDIN_DRAFT_*.md (already in Pending_Approval/)

SKILL_Reasoning_Loop
  → any step in a plan that hits triggers #1–#10
  → calls SKILL_HITL_Approval → marks parent plan step as [~]
  → plan pauses until /Approved/ or /Rejected/ decision

SKILL_Process_Needs_Action
  → catches any item not handled by the above
  → calls SKILL_HITL_Approval for trigger matches before processing
```

---

## Rules Checklist (verify before writing any Pending_Approval file)

- [ ] `type: approval_request` and correct `subtype:` are set
- [ ] `action:` field is a single sentence describing exactly what will happen if approved
- [ ] `mcp_trigger:` is set to the correct MCP server (or `none`)
- [ ] `expires:` is set to 24 hours from `created:` (per Handbook Section 4)
- [ ] `source_file:` references the originating item
- [ ] If mid-plan: `plan_ref:` is set and parent plan step is marked `[~]` blocked
- [ ] Dashboard Pending Approvals table has been updated
- [ ] Claude has **not** taken the action — the file is the only output of this skill

---

*Silver Tier Agent Skill — the canonical HITL gate. All external actions pass through here.*
