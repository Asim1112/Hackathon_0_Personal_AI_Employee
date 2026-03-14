# SKILL_Facebook_Instagram — Agent Skill

## Purpose
Draft Facebook Page posts and Instagram content for human approval before publishing
via `facebook-instagram-mcp`. Process engagement alerts from `Needs_Action/`.
No post is ever published directly — all go through the HITL approval gate.

---

## When to Invoke

- User asks to "post on Facebook/Instagram" or "draft a social post"
- `facebook_watcher.py` drops a `FACEBOOK_<date>_<id>.md` or `INSTAGRAM_<date>_<id>.md` in `Needs_Action/`
- Orchestrator asks for weekly content
- Content from LinkedIn or Twitter can be repurposed for Facebook/Instagram

---

## Platform Differences

### Facebook Page
- Longer-form content allowed (up to 63,206 chars, but 1–3 paragraphs is optimal)
- Can include links (they show preview cards)
- Can target specific audiences
- Best for: articles, announcements, event promotions, blog-style content

### Instagram
- No clickable links in captions (only in bio/stories)
- Caption limit: 2,200 characters
- Hashtags are important for reach (up to 30, but 5–10 is optimal)
- Best for: visual content, behind-the-scenes, testimonials
- **Note:** Image URL must be provided — this MCP does not generate images

---

## Content Strategy

Read `Company_Handbook.md` → **Social Media Voice** section for tone guidelines.

### Content Pillars (same as Twitter)
1. **AI & Automation insights** — educational, thought leadership
2. **Client results** — social proof (with permission)
3. **Behind-the-scenes** — building the AI Employee
4. **Industry news & commentary**

### Tone
- Warmer and more conversational than Twitter
- Facebook: can be slightly longer, include a question to drive comments
- Instagram: concise, visual-first, strong hook in first line

---

## What You Write

### Facebook Post

Create `Pending_Approval/FACEBOOK_DRAFT_<SlugTitle>_<YYYY-MM-DD>.md`:

```markdown
---
type: social_post
platform: facebook
send_via_mcp: facebook-instagram-mcp
action: post_facebook
status: pending
created: <ISO timestamp>
content_pillar: <insights|results|behind_scenes|commentary>
logged: false
---

## Facebook Draft: <Title>

**Context:** <1 sentence — why this post, what triggered it>

---

### Post Content

<Full Facebook post text. Can be 1–3 paragraphs. End with a question or CTA.>

---

### Why This Content

<2–3 sentences: value to followers, why now>

### Action Data
```json
{
  "platform": "facebook",
  "message": "<full post text>",
  "link": "<optional URL to include>",
  "link_name": "<optional link title>"
}
```

> ⚠️ **Human approval required.**
> Move to `/Approved/` to publish via facebook-instagram-mcp.
```

---

### Instagram Post

Create `Pending_Approval/INSTAGRAM_DRAFT_<SlugTitle>_<YYYY-MM-DD>.md`:

```markdown
---
type: social_post
platform: instagram
send_via_mcp: facebook-instagram-mcp
action: post_instagram
status: pending
created: <ISO timestamp>
content_pillar: <insights|results|behind_scenes|commentary>
image_required: true
logged: false
---

## Instagram Draft: <Title>

**Context:** <1 sentence — why this post>

---

### Caption

<Instagram caption. Strong hook first line. 150–300 chars optimal.
No clickable links — direct to bio link if needed.>

<Hashtags on separate line:>
#hashtag1 #hashtag2 #hashtag3

---

### Image/Visual Notes

**Image required:** Yes — Instagram posts need a visual.
**Suggested visual:** <description of ideal image or graphic>
**If no image is available:** Cannot post to Instagram — create Facebook post instead.

### Action Data
```json
{
  "platform": "instagram",
  "caption": "<full caption with hashtags>",
  "image_url": "<URL of image to post — REQUIRED>"
}
```

> ⚠️ **Human approval required.**
> You must add a valid `image_url` to the action data before moving to `/Approved/`.
> facebook-instagram-mcp will NOT post without an image URL.
```

---

## Repurposing Content from Other Platforms

When repurposing LinkedIn or Twitter content for Facebook/Instagram:

| Source | Facebook adaptation | Instagram adaptation |
|--------|--------------------|--------------------|
| LinkedIn post | Expand slightly, add question | Condense to hook + key point + hashtags |
| Tweet/thread | Expand to paragraph form | Keep concise, add hashtags |
| CEO Briefing insight | Write as narrative post | Key stat + context + CTA |

Always adapt the tone — don't just copy-paste.

---

## Processing Engagement Alerts

When `facebook_watcher.py` drops a file in `Needs_Action/`:

### Comments on Posts
- Positive comment: optionally draft a brief reply in Pending_Approval/
- Question in comment: draft a helpful reply
- Complaint: write to Pending_Approval/ as HUMAN_REVIEW, do NOT auto-reply

### Page Messages / DMs
- Draft reply to `Inbox/` using same pattern as email drafts
- Flag as new contact if first interaction → follow `SKILL_HITL_Approval` new contact rule

### Mentions
- Note in `Social_Analytics/Facebook_Instagram_Summary.md`
- If relevant for resharing → draft a response

---

## After Writing the Draft

1. Update `Needs_Action/` trigger file: `status: processed`
2. Move trigger to `Done/`
3. Log to `Logs/YYYY-MM-DD.json`:
   ```json
   {
     "action_type": "facebook_post_drafted",
     "source": "claude_code",
     "target": "Pending_Approval/FACEBOOK_DRAFT_<slug>.md",
     "skill_used": "SKILL_Facebook_Instagram",
     "approval_status": "pending",
     "result": "success",
     "notes": "<brief description>"
   }
   ```
4. Update `Social_Analytics/Facebook_Instagram_Summary.md` if new metrics available

---

## What NOT to Do

- ❌ Never publish directly — always write to `Pending_Approval/`
- ❌ Never post to Instagram without an `image_url` in the action data
- ❌ Never reply to complaints without human review
- ❌ Never use personal account content (this is always the Business Page)
- ❌ Never include competitor names in posts
