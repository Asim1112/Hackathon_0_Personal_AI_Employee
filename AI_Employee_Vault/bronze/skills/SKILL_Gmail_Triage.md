---
skill: gmail_triage
version: 1.0
trigger: manual
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
  - Needs_Action/*.md  (updates priority/status fields only — file stays here for SKILL_Process_Needs_Action)
  - Inbox/DRAFT_REPLY_*.md  (reply drafts — never sent directly)
  - Pending_Approval/EMAIL_REVIEW_*.md  (sensitive escalations)
  - Dashboard.md  (Pending Messages section)
created: 2026-02-24
---

# SKILL: Gmail Triage

## What This Skill Does

Reads all `type: email` files in `Needs_Action/`, applies the communication rules
from `Company_Handbook.md`, assigns or verifies priority, drafts replies where
appropriate, escalates sensitive items, and updates the Dashboard.

**This skill triages — it does not move files to Done/.**
Run `SKILL_Process_Needs_Action` after this to complete the cycle.

---

## When to Run This Skill

Run this skill when:
- New email `.md` files appear in `Needs_Action/`
- You are asked to "triage emails", "check the inbox", or "handle messages"
- Before running `SKILL_Process_Needs_Action` when emails are present

---

## Pre-Conditions (check before starting)

- [ ] Read `Company_Handbook.md` — Section 1 (Communication Rules) in full
- [ ] Note the `Payment Approval Limit` from Company_Handbook.md Section 8
- [ ] Note the `Key Contacts` table from Company_Handbook.md Section 9
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

| Field         | Source                    |
|---------------|---------------------------|
| Sender name   | `from:` header            |
| Sender email  | `from:` header (parse)    |
| Subject       | `subject:` header         |
| Date sent     | `date_sent:` header       |
| Body preview  | `## Email Body` section   |
| Current priority | `priority:` frontmatter |

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
| Payment request over the Company_Handbook threshold | Financial rule |
| Sender is unknown AND subject is vague or suspicious | Unknown risk |

Action: Write an escalation file to `Pending_Approval/` (see format below). Mark email file `status: escalated`.

---

#### 🟡 DRAFT REPLY → Inbox/

Draft a reply if the email is:
- A question or request from a known contact
- A routine follow-up or information request
- A meeting request or scheduling query
- A client update that warrants acknowledgement

Action: Write a draft to `Inbox/DRAFT_REPLY_<subject-slug>_<date>.md`. Do NOT send. Mark email `triage_action: draft_written`.

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
| From a Key Contact (Company_Handbook Section 9) | `high` minimum |
| Contains deadline date within 48 hours | `urgent` |
| Contains deadline date within 7 days | `high` |
| Routine query, no deadline | `medium` |
| Newsletter / notification | `low` |

Update the frontmatter in-place if priority changes.

---

### Step 5 — Write triage summary into each email file

Add a `## Triage Notes` section immediately before `## Processing Notes`:

```markdown
## Triage Notes

**Triaged:** 2026-02-24T10:00:00Z
**Classification:** <ESCALATE | DRAFT_REPLY | LOG_ONLY | HUMAN_REVIEW>
**Priority confirmed:** <urgent | high | medium | low>
**Sender known:** <Yes — [contact role] | No — unknown sender>
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
created: 2026-02-24T10:00:00Z
status: draft
approved: false
---

# Draft Reply: Re: <original subject>

> ⚠️ This is a DRAFT. Review before sending. Not sent automatically.

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

Rewrite the `## Pending Messages` section in `Dashboard.md` to reflect the
current triage state. One row per email still in `Needs_Action/`:

```markdown
## Pending Messages

| # | Source | From | Subject / Preview | Received | Priority |
|---|--------|------|-------------------|----------|----------|
| 1 | gmail  | Sender Name | Subject line here | 2026-02-24 | 🔴 urgent |
| 2 | gmail  | Sender Name | Subject line here | 2026-02-24 | 🟡 high   |
```

Priority emoji guide:
- 🔴 `urgent` — needs immediate human attention
- 🟡 `high` — handle within 4 hours
- 🟢 `medium` — handle within 24 hours
- ⚪ `low` — handle within 72 hours

---

### Step 8 — Output triage report

Print a summary:

```
📬 Gmail Triage Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total emails triaged:  N
  🔴 Escalated:          N  → written to Pending_Approval/
  🟡 Draft replies:      N  → written to Inbox/
  🟢 Log only:           N  → noted, no action
  ⚪ Human review:       N  → flagged in Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
escalation_reason: "<legal | financial | complaint | security | unknown>"
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
2. <Option B — e.g. "Forward to solicitor">
3. <Option C — e.g. "Ignore / archive">

## To Approve an Action

Edit this file: set `status: approved` and add `approved_action: <chosen option>`,
then move to `/Approved` folder.

## To Reject / No Action

Move this file to `/Rejected` folder.

---
*Escalated by Claude Gmail Triage — awaiting human decision.*
```

---

## Rules Reference (Company_Handbook.md)

| Rule | Section | Applied in Step |
|---|---|---|
| Always be polite on WhatsApp/email | Section 1 | Step 6 (draft tone) |
| Flag payments over threshold | Section 2 | Step 3 (ESCALATE) |
| Never send directly — drafts only | Section 1 | Step 6 (draft to Inbox/) |
| Legal/complaint → human review | Section 4 | Step 3 (ESCALATE) |
| Reply within 24h or escalate | Section 1 | Step 3 classification |
| Key contacts get priority treatment | Section 9 | Step 4 (priority bump) |

---

## Usage Examples

### Example 1 — Triage all pending emails

```
Use SKILL_Gmail_Triage to triage all emails currently in Needs_Action/.
```

### Example 2 — Triage then process

```
1. Use SKILL_Gmail_Triage to triage all emails in Needs_Action/.
2. Then use SKILL_Process_Needs_Action to process everything not escalated.
```

### Example 3 — Targeted single email

```
Use SKILL_Gmail_Triage on Needs_Action/EMAIL_2026-02-24_Invoice_abc123.md only.
```

### Example 4 — Morning routine

```
Good morning. Use SKILL_Gmail_Triage followed by SKILL_Process_Needs_Action
to handle everything that came in overnight. Update Dashboard.md when done.
```

---

*Bronze Tier Agent Skill — reads/writes vault only, no external send actions.*
