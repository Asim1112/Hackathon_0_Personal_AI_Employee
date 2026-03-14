# SKILL_Twitter_Draft — Agent Skill

## Purpose
Draft tweets and thread content for human approval before posting via `twitter-mcp`.
Never post directly — always write to `Pending_Approval/`.

---

## When to Invoke

- A file in `Needs_Action/` has `type: twitter` (mention, DM, or scheduled post trigger)
- User asks to "draft a tweet" or "write a thread about X"
- LinkedIn post being repurposed for Twitter
- Weekly social content batch (from orchestrator.py)

---

## Twitter Content Principles

1. **Brevity:** Standard tweets ≤ 280 characters. Count carefully.
2. **Threads:** Use for content > 280 chars. Number tweets 1/n.
3. **Hashtags:** Max 2–3 relevant hashtags. Don't over-tag.
4. **Tone:** Professional but conversational. Match the brand voice in `Company_Handbook.md`.
5. **Engagement hooks:** Start with a strong first line — it's what gets seen in feeds.
6. **CTAs:** Only one call-to-action per tweet/thread (if any).
7. **No empty hype:** No generic "Excited to announce…" — be specific.

---

## Processing Twitter Mentions / DMs

When `twitter_watcher.py` drops a mention or DM in `Needs_Action/`:

1. Read the file frontmatter and content
2. Classify the intent:
   - **Sales enquiry** → draft DM reply + flag for `SKILL_Gmail_Triage` follow-up
   - **Support question** → draft public reply or DM (check if public reply is appropriate)
   - **Positive mention** → optional like/retweet acknowledgement note for human
   - **Negative mention** → escalate to `Pending_Approval/` as `HUMAN_REVIEW` — never auto-respond to complaints
   - **Spam/bot** → note in file, move to `Done/` with `result: ignored`
3. Draft the response
4. Write to `Pending_Approval/`

---

## Drafting a Tweet or Thread

### Single tweet

````markdown
---
type: social_draft
platform: twitter
send_via_mcp: twitter-mcp
status: pending
created: <ISO timestamp>
char_count: <n>
logged: false
---

## Twitter Draft — <topic>

### Tweet
<tweet text — max 280 chars>

**Character count:** <n>/280

### Context
<Why this tweet? What's the goal? What should it link to?>

### Hashtags
`#<tag1>` `#<tag2>`

### Posting Notes
- Suggested time: <weekday HH:MM>

```json
{
  "action": "post_tweet",
  "content": "<tweet text — max 280 chars>"
}
```
````

### Thread (3+ tweets)

````markdown
---
type: social_draft
platform: twitter
send_via_mcp: twitter-mcp
content_type: thread
tweet_count: <n>
status: pending
created: <ISO timestamp>
logged: false
---

## Twitter Thread Draft — <topic>

### Tweet 1/n (Hook)
<280 chars max>

### Tweet 2/n
<280 chars max>

### Tweet 3/n (CTA)
<280 chars max>

### Thread Context
<Purpose and target audience of this thread>

```json
{
  "action": "post_tweet",
  "thread": [
    "<tweet 1 text>",
    "<tweet 2 text>",
    "<tweet 3 text>"
  ]
}
```
````

---

## Replying to a Mention

````markdown
---
type: social_draft
platform: twitter
send_via_mcp: twitter-mcp
content_type: reply
reply_to_tweet_id: <tweet_id from the trigger file>
status: pending
created: <ISO timestamp>
logged: false
---

## Twitter Reply Draft

**Replying to:** @<username> — "<original tweet excerpt>"

### Reply
<tweet text — max 280 chars>

**Character count:** <n>/280

### Rationale
<Why this response? Tone choice?>

```json
{
  "action": "reply_tweet",
  "reply_to_tweet_id": "<tweet_id>",
  "content": "<reply text — max 280 chars>"
}
```
````

---

## After Writing the Draft

1. Update `Needs_Action/` source file: `status: processed`, `processed_at: <now>`
2. Move source file to `Done/`
3. Log to `Logs/YYYY-MM-DD.json` with `action_type: twitter_draft_created`
4. Note in `Dashboard.md` → Pending Approvals table

---

## What NOT to Do

- ❌ Do NOT post directly — always `Pending_Approval/` first
- ❌ Do NOT respond to negative mentions without human review
- ❌ Do NOT exceed 280 characters on a single tweet (count carefully)
- ❌ Do NOT use more than 3 hashtags
- ❌ Do NOT fabricate engagement metrics
