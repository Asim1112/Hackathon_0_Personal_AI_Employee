---
type: instagram
status: processed
processed_at: 2026-04-14T08:45:00Z
platform: instagram
instagram_type: post_request
source: admin_task
topic: "Personal AI Employee system — visual announcement for Instagram audience"
tone: professional
image_url: https://i.postimg.cc/Hnm43D2q/Gemini-Generated-Image-w0ch6pw0ch6pw0ch.png
received: 2026-04-14T08:30:00Z
priority: normal
logged: false
---

# Instagram Post Request — AI Employee Visual Announcement

**Type:** Admin task — Instagram Business account post
**Source:** Scheduled content batch
**Received:** 2026-04-14 08:30 UTC

---

## Brief

Write an Instagram post caption to accompany the provided image announcing the Gold Tier Personal AI Employee system.

**Image URL (mandatory — do not change):**
https://i.postimg.cc/Hnm43D2q/Gemini-Generated-Image-w0ch6pw0ch6pw0ch.png

**Key messages:**
1. AI Employee monitors Email, LinkedIn, Twitter, Facebook, and Odoo simultaneously
2. Every action requires human approval before execution — full HITL control
3. Built for professional services businesses

**Tone:** Professional, concise, Instagram-appropriate
**Format:** 3–5 sentences + 5–8 relevant hashtags on a new line
**Constraints:** No generic openers like "Excited to share", keep it under 300 words

---

## Action Required

Use SKILL_Facebook_Instagram to draft an Instagram post and write to `Pending_Approval/` with exact frontmatter:
- `type: social_post`
- `platform: instagram`
- `send_via_mcp: facebook-instagram-mcp`
- `action: post_instagram`
- `image_url: https://i.postimg.cc/Hnm43D2q/Gemini-Generated-Image-w0ch6pw0ch6pw0ch.png`

Include Action Data JSON block with BOTH `"caption"` AND `"image_url"` fields. The image_url MUST be:
https://i.postimg.cc/Hnm43D2q/Gemini-Generated-Image-w0ch6pw0ch6pw0ch.png
