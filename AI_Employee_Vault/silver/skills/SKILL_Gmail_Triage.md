---
skill: gmail_triage
version: 2.0
tier: silver
trigger: manual | scheduled (8 AM daily)
inputs:
  - Needs_Action/*.md files where type: email and status: pending
outputs:
  - Priority assigned and verified on each email file
  - Draft replies written to Inbox/ where appropriate
  - Sensitive emails escalated to Pending_Approval/
  - Dashboard.md Pending Messages table updated
reads:
  - Needs_Action/*.md  (type: email only)
  - Company_Handbook.md
  - Dashboard.md
writes:
  - Needs_Action/*.md  (updates priority/status fields only)
  - Inbox/DRAFT_REPLY_*.md  (reply drafts — never sent directly)
  - Pending_Approval/EMAIL_REVIEW_*.md  (sensitive escalations)
  - Dashboard.md  (Pending Messages section)
created: 2026-02-25
---

# SKILL: Gmail Triage (Silver Tier)

## What This Skill Does

Reads all `type: email` files in `Needs_Action/`, applies the communication rules
from `Company_Handbook.md`, assigns or verifies priority, drafts replies where
appropriate, escalates sensitive items, and updates the Dashboard.

**Silver changes from Bronze:**
- HITL threshold is now £50 (not £500) — escalate any financial email over £50
- Any email from a **new contact** (not in Key Contacts) → write to `Pending_Approval/` before replying
- Email replies drafted to `Inbox/` — MCP server sends only after `/Approved/` trigger

**This skill triages — it does not move files to Done/.**
Run `SKILL_Process_Needs_Action` after this to complete the cycle.

---

## When to Run This Skill

Run this skill when:
- New email `.md` files appear in `Needs_Action/`
- You are asked to "triage emails", "check the inbox", or "handle messages"
- The scheduled 8 AM daily run triggers the full workflow

---

## Pre-Conditions (check before starting)

- [ ] Read `Company_Handbook.md` — Section 1 (Communication), Section 4 (HITL), Section 11 (Key Contacts)
- [ ] Note the `Payment Approval Limit` from Company_Handbook.md Section 10 (**£50** for Silver)
- [ ] Note the `Key Contacts` table from Company_Handbook.md Section 11
- [ ] Read current `Dashboard.md` Pending Messages section

---

## Step-by-Step Instructions

### Step 1 — Identify all email files

List every file in `Needs_Action/` where:
- `type: email`
- `status: pending`

If none found, output: `No pending emails in Needs_Action/ — triage complete.` and stop.

---

### Step 2 — For each email, read and extract

From the file frontmatter and body, extract:

| Field          | Source                   |
|----------------|--------------------------|
| Sender name    | `from:` header           |
| Sender email   | `from:` header (parse)   |
| Subject        | `subject:` header        |
| Date sent      | `date_sent:` header      |
| Body preview   | `## Email Body` section  |
| Current priority | `priority:` frontmatter|
| Is new contact | Check against Section 11 |

---

### Step 3 — Classify the email

Assign one classification per email. Use the first matching rule:

#### 🔴 ESCALATE → Pending_Approval/ (do not draft reply, human must handle)

Escalate immediately if the email contains ANY of:

| Trigger | Reason |
|---|---|
| Words: `legal`, `lawsuit`, `court`, `solicitor`, `claim`, `liability` | Legal risk |
| Words: `complaint`, `dispute`, `chargeback`, `refund demand` | Reputational risk |
| Words: `threat`, `breach`, `hack`, `compromised` | Security risk |
| Payment request over **£50** | Financial HITL (Silver rule) |
| **Sender is a new contact** (not in Key Contacts Section 11) | Silver HITL rule |
| Unknown sender AND vague or suspicious subject | Unknown risk |

Action: Write an escalation file to `Pending_Approval/` (see format below). Mark email file `status: escalated`.

---

#### 🟡 DRAFT REPLY → Inbox/

Draft a reply if the email is:
- A question or request from a **known Key Contact**
- A routine follow-up or information request (under £50, known sender)
- A meeting request or scheduling query
- A client update that warrants acknowledgement

Action: Write a draft to `Inbox/DRAFT_REPLY_<subject-slug>_<date>.md`. Do NOT send. Mark email `triage_action: draft_written`.

> Note: The email MCP will send this draft only after human moves it to `/Approved/`.

---

#### 🟢 LOG ONLY → no draft needed

Log-only if the email is:
- A newsletter, notification, or automated message
- A receipt or confirmation with no required action
- An FYI with no question or request

Action: Add a note to the Processing Notes section. Mark email `triage_action: log_only`.

---

#### ⚪ HUMAN REVIEW → flag in Dashboard

Flag for human review if:
- Classification is genuinely ambiguous
- The email is from an unknown sender and contains a proposal or pitch
- The content references a project or context Claude has no record of

Action: Mark email `triage_action: human_review`. Add to Dashboard Pending Messages with flag.

---

### Step 4 — Re-evaluate priority

After classification, confirm or update the `priority:` frontmatter field:

| Condition | Set priority |
|---|---|
| Escalated to Pending_Approval | `urgent` |
| New contact (Silver HITL) | `high` minimum |
| From a Key Contact (Section 11) | `high` minimum |
| Contains deadline within 48 hours | `urgent` |
| Contains deadline within 7 days | `high` |
| Routine query, no deadline | `medium` |
| Newsletter / notification | `low` |

Update the frontmatter in-place if priority changes.

---

### Step 5 — Write triage summary into each email file

Add a `## Triage Notes` section immediately before `## Processing Notes`:

```markdown
## Triage Notes

**Triaged:** 2026-02-25T10:00:00Z
**Classification:** <ESCALATE | DRAFT_REPLY | LOG_ONLY | HUMAN_REVIEW>
**Priority confirmed:** <urgent | high | medium | low>
**Sender known:** <Yes — [contact role] | No — new contact → HITL required>
**HITL triggered:** <Yes — reason | No>
**Key points:**
- <Bullet 1: what this email is actually about>
- <Bullet 2: any deadline or financial figure mentioned>
- <Bullet 3: sentiment — neutral / positive / negative / urgent>
**Triage action:** <what was done — draft written / escalated / logged>
```

---

### Step 6 — Write draft replies (where applicable)

For emails classified as DRAFT_REPLY, write a reply draft to `Inbox/`:

**Filename:** `DRAFT_REPLY_<subject-slug>_<YYYY-MM-DD>.md`

**Format:**

```markdown
---
type: draft_reply
in_reply_to_file: "<original email filename in Needs_Action/>"
in_reply_to_gmail_id: "<gmail_id from original>"
to: "<sender email>"
subject: "Re: <original subject>"
created: 2026-02-25T10:00:00Z
status: draft
approved: false
send_via_mcp: email-mcp
---

# Draft Reply: Re: <original subject>

> ⚠️ This is a DRAFT. Review before sending.
> To send: move this file to /Approved/ — the email MCP will send it automatically.

---

<Salutation — match formality of original email>,

<Opening sentence acknowledging their message>

<Body: 2-3 short paragraphs addressing their question or request>
- Use first-person ("I will...", "I can confirm...")
- Be polite, clear, and solution-oriented (per Company_Handbook Section 1)
- Never promise timelines or prices without verification
- Never mention competitors

<Closing — e.g. "Please let me know if you have any questions.">

<Sign-off>,
[YOUR NAME]
[YOUR BUSINESS NAME]

---

*Draft generated by Claude — review and approve before sending.*
```

---

### Step 7 — Update Dashboard.md Pending Messages table

Rewrite the `## Pending Messages` section in `Dashboard.md`:

```markdown
## Pending Messages

| # | Source | From | Subject / Preview | Received | Priority |
|---|--------|------|-------------------|----------|----------|
| 1 | gmail  | Sender Name | Subject line | 2026-02-25 | 🔴 urgent |
| 2 | gmail  | Sender Name | Subject line | 2026-02-25 | 🟡 high   |
```

Priority emoji guide:
- 🔴 `urgent` — needs immediate human attention
- 🟡 `high` — handle within 4 hours
- 🟢 `medium` — handle within 24 hours
- ⚪ `low` — handle within 72 hours

---

### Step 8 — Output triage report

```
📬 Gmail Triage Complete (Silver Tier)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total emails triaged:     N
  🔴 Escalated:             N  → written to Pending_Approval/
  🟡 Draft replies:         N  → written to Inbox/ (MCP-ready)
  🟢 Log only:              N  → noted, no action
  ⚪ Human review:          N  → flagged in Dashboard
  ⚡ HITL triggered:        N  → new contacts / over £50
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run SKILL_Process_Needs_Action to complete processing.
```

---

## Escalation File Format (Pending_Approval/)

**Filename:** `EMAIL_REVIEW_<subject-slug>_<YYYY-MM-DD>.md`

```markdown
---
type: approval_request
subtype: email_escalation
source_file: "<original email filename>"
from: "<sender>"
subject: "<email subject>"
escalation_reason: "<legal | financial_over_50 | new_contact | complaint | security | unknown>"
created: <ISO timestamp>
expires: <ISO timestamp — 24h later>
status: pending
---

## Why This Was Escalated

<One paragraph: what the email contains and which handbook rule triggered escalation>

## Original Email Summary

**From:** <sender>
**Subject:** <subject>
**Key content:** <2-3 sentence summary>

## Suggested Response Options

1. <Option A — e.g. "Reply with standard acknowledgement">
2. <Option B — e.g. "Forward to relevant person">
3. <Option C — e.g. "Ignore / archive">

## To Approve a Reply

Edit this file: set `status: approved` and add `approved_action: <chosen option>`,
then move to `/Approved/` folder — the email MCP will send the reply.

## To Reject / No Action

Move this file to `/Rejected/` folder.

---
*Escalated by Claude Gmail Triage (Silver) — awaiting human decision.*
```

---

*Silver Tier Agent Skill — drafts to Inbox/, escalations to Pending_Approval/, MCP sends on /Approved/ trigger.*
