---
skill: whatsapp_triage
version: 1.0
tier: silver
trigger: called by SKILL_Process_Needs_Action when type: whatsapp is found in Needs_Action/
inputs:
  - Needs_Action/*.md  where type: whatsapp and status: pending
outputs:
  - Inbox/DRAFT_WA_REPLY_*.md        (known contacts — awaiting human approval before send)
  - Pending_Approval/NEW_CONTACT_REVIEW_*.md  (new contacts — HITL required)
  - Pending_Approval/COMPLAINT_REVIEW_*.md    (complaints — never handle autonomously)
  - Triage notes written into each source file
reads:
  - Needs_Action/*.md  (type: whatsapp)
  - Company_Handbook.md  (Section 1 WhatsApp rules, Section 4 HITL, Section 11 Key Contacts)
  - Dashboard.md
writes:
  - Needs_Action/*.md  (triage notes + status update in-place)
  - Inbox/DRAFT_WA_REPLY_*.md
  - Pending_Approval/*.md  (HITL escalations)
  - Dashboard.md  (Pending Messages table)
called_by: SKILL_Process_Needs_Action
calls: SKILL_HITL_Approval  (new contacts, complaints, time-gated)
created: 2026-02-25
---

# SKILL: WhatsApp Triage (Silver Tier)

## What This Skill Does

Processes all `type: whatsapp` files in `Needs_Action/` produced by `whatsapp_watcher.py`.
Applies the WhatsApp communication rules from `Company_Handbook.md`, classifies each
message, drafts replies for known contacts, and escalates via `SKILL_HITL_Approval` for
anything that requires human sign-off before sending.

**WhatsApp is higher-risk than email** — replies go to personal phone numbers.
The time gate, new-contact rule, and complaint block are non-negotiable.

---

## When to Run This Skill

Run this skill when:
- `SKILL_Process_Needs_Action` routes a `type: whatsapp` item here
- The daily 8 AM cycle finds WhatsApp items in the queue
- You are asked to “triage WhatsApp messages” or “check WhatsApp”

**Do not run on files with `status: processed` or `status: escalated`.**
