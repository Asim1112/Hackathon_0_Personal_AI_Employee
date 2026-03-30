---
type: facebook
status: processed
processed_at: 2026-03-26T09:45:00Z
platform: facebook
facebook_type: post_request
source: admin_task
topic: "Personal AI Employee system — business announcement for professional services audience"
tone: professional
received: 2026-03-26T08:20:00Z
priority: normal
logged: false
---

# Facebook Post Request — Business Announcement

**Type:** Admin task — Facebook Business Page post
**Source:** Scheduled content batch
**Received:** 2026-03-26 08:20 UTC

---

## Brief

Write a Facebook Business Page post announcing the Gold Tier Personal AI Employee system.

**Key messages to convey:**
1. The system monitors Email, LinkedIn, Twitter, Facebook, and Odoo ERP simultaneously
2. Every outbound action (email send, social post, invoice creation) requires explicit human approval before execution
3. Full audit trail on every action — nothing happens without a record
4. Designed for professional services businesses and consultancies

**Tone:** Professional, authoritative, accessible — written for business owners and operations managers, not developers.

**Format:** 2–4 paragraphs. End with a question or call-to-action to encourage engagement.

**Constraints:**
- No emojis unless they add genuine value
- No generic phrases like "We're thrilled to share"
- Specific and concrete — mention actual capabilities, not vague promises
- Do NOT include any URLs

---

## Action Required

Use SKILL_Facebook_Instagram to draft a Facebook post and write to `Pending_Approval/` with exact frontmatter:
- `type: social_post`
- `send_via_mcp: facebook-instagram-mcp`
- `action: post_facebook`

And include Action Data JSON block with `"message"` field containing the full post text.
