---
type: approval_request
action: send_whatsapp_reply
channel: whatsapp
mcp_server: none
source_file: "Needs_Action/WHATSAPP_TEST_2026-02-25_John_Smith_test1234.md"
contact: "John Smith"
contact_tier: 4
priority: high
status: pending
created: 2026-03-09T08:00:00Z
expires: 2026-03-10T08:00:00Z
generated_by: SKILL_WhatsApp_Triage
---

# NEW CONTACT REVIEW — John Smith (WhatsApp)

## Why This Requires Approval

Per Company Handbook Section 3.2.2: First message to unknown sender requires HITL approval.
John Smith is NOT in Key Contacts (Section 8) — classified as **Tier 4 General**.

---

## Original Message Summary

**From:** John Smith (WhatsApp)
**Keyword Matched:** `invoice`
**Received:** 2026-03-08T21:12Z (Sunday — queued for Monday)
**Content:** "Hi, just checking on the invoice you sent last week — can you confirm it's been received? Need to process ASAP, thanks."

---

## Triage Analysis

- **Contact tier:** 4 (unknown — not in Key Contacts)
- **Priority:** HIGH (invoice keyword + ASAP)
- **Financial flag:** Invoice mentioned — verify internally before replying (no amounts stated)
- **New contact rule:** First message → HITL mandatory
- **Time gate:** Received 21:12 Sunday (outside hours), now processed Monday 08:00 (within gate) ✅
- **MCP available:** ❌ None — WhatsApp reply must be sent **manually by human**

---

## What Claude Considered

Could draft a holding reply confirming receipt of the invoice query. However, as a new contact referencing a specific invoice, you should verify: (a) do you know who John Smith is? (b) have you actually sent an invoice to this person? The reference to "the invoice you sent" implies a pre-existing business relationship.

---

## What Human Should Decide

1. **Do you know John Smith?** If yes, assign them a tier in Key Contacts.
2. **Is the invoice referenced legitimate?** If yes, approve the reply below.
3. **Is this potentially fraudulent/phishing?** If uncertain, reject and do not engage.

---

## Proposed Reply Draft

> Hi John,
>
> Thanks for your message. Yes, the invoice has been sent — please do let me know if you haven't received it and I'll resend straight away. Happy to confirm any details you need to process it.
>
> Best,
> [Your Name]

---

## Action Required

| Option | How | Result |
|--------|-----|--------|
| ✅ **Approve** | Move this file to `Approved/` | Send the draft reply manually via WhatsApp |
| ❌ **Reject** | Move this file to `Rejected/` | No reply sent |

> ⚠️ WhatsApp has no MCP server. After approving, you must send the reply manually via your phone or WhatsApp Web.

---

*Created by SKILL_WhatsApp_Triage at 2026-03-09T08:00:00Z*
*Expires: 2026-03-10T08:00:00Z (auto-rejected after 24h)*
