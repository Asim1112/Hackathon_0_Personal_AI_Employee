---
type: business_goals
tier: gold
last_updated: 2026-03-11
review_frequency: weekly
for: Claude Code — read during every cycle and always before generating CEO Briefing
---

# Business Goals & KPIs

> This file is your operating targets. Read it before every processing cycle.
> Claude uses this during SKILL_Weekly_CEO_Briefing to measure actual vs target performance.
> **Do not modify this file yourself.** The human owner updates targets here.

---

## Q1 2026 Objectives

### Revenue Target

| Metric             | Target       | Current MTD  | Status |
|--------------------|--------------|--------------|--------|
| Monthly Revenue    | £10,000      | £0.00        | ⚪ Not synced |
| Weekly Average     | £2,500       | —            | ⚪ Not synced |
| Outstanding (AR)   | < £2,000     | —            | ⚪ Not synced |
| Invoice Payment Rate | > 90%      | —            | ⚪ Not synced |

### Key Performance Metrics

| Metric                     | Target           | Alert Threshold  | Source     |
|----------------------------|------------------|------------------|------------|
| Client email response time | < 24 hours       | > 48 hours       | Gmail      |
| Tier 1 client SLA          | < 2 hours        | > 4 hours        | Gmail      |
| Invoice payment rate       | > 90%            | < 80%            | Odoo       |
| Monthly software costs     | < £500/month     | > £600/month     | Odoo       |
| LinkedIn engagement rate   | > 3%             | < 1%             | LinkedIn   |
| Twitter impressions (7d)   | > 1,000          | < 200            | Twitter    |
| New leads per week         | 2+               | 0                | All channels |

---

## Active Projects

| Project Name | Client | Budget | Due Date | Status |
|--------------|--------|--------|----------|--------|
| AI Employee Hackathon | Internal | — | — | 🟡 In Progress |
| _(Add real projects here)_ | — | — | — | — |

---

## Service Offerings & Rates

| Service | Rate | Min Hours | Notes |
|---------|------|-----------|-------|
| AI Consulting | £150/hr | 2 hrs | HITL approval required for quotes |
| System Integration | £120/hr | 4 hrs | — |
| Training / Workshop | £500/day | 1 day | — |
| Retainer | £2,000/mo | — | Priority SLA override |

---

## Subscription Audit Rules

Flag for review in CEO Briefing if ANY of the following are true:
- No usage/login in **30 days**
- Cost increased **> 20%** since last review
- Duplicate functionality with another tool
- Monthly cost **> £50** with no documented value

### Current Subscriptions

| Tool | Monthly Cost | Last Reviewed | Status |
|------|-------------|---------------|--------|
| Claude Code (Pro) | £18 | 2026-03-11 | ✅ Active |
| _(Add your subscriptions here)_ | — | — | — |

---

## Weekly Audit Checklist (for SKILL_Weekly_CEO_Briefing)

Claude MUST check each of these every Sunday and include in the CEO Briefing:

- [ ] Revenue this week vs weekly target (£2,500)
- [ ] Outstanding invoices older than 14 days
- [ ] Overdue invoices (past payment terms)
- [ ] Completed tasks count (from `Done/` folder — files created this week)
- [ ] SLA breaches this week (emails > 48h unanswered)
- [ ] Pending approvals older than 24h (potential bottleneck)
- [ ] Social media posts this week (LinkedIn + Twitter + FB/IG)
- [ ] New leads captured this week
- [ ] Subscription audit: any flagged for review

---

## Business Rules for CEO Briefing

### Revenue Classification
- **On Track:** MTD revenue ≥ 80% of pro-rated monthly target
- **Behind:** MTD revenue 60-79% of pro-rated target
- **At Risk:** MTD revenue < 60% of pro-rated target

### Bottleneck Definition
A task is a bottleneck if:
- It remained in `Pending_Approval/` for more than 24 hours
- It triggered an SLA breach
- It required more than 3 plan steps and is still `in_progress`

### Proactive Suggestion Triggers
Claude MUST suggest an action in the CEO Briefing when:
- An invoice has been outstanding > 14 days → "Chase Client X for payment"
- A subscription hasn't been used in 30 days → "Consider cancelling"
- A lead has been in `Pending_Approval/` > 48h → "Follow up urgently"
- Monthly software costs exceed £500 → "Review subscriptions"

---

## Contact Tiers (Reference)

| Tier | Label | SLA | Examples |
|------|-------|-----|---------|
| 1 | Strategic Client | 2h response | _(add your Tier 1 clients)_ |
| 2 | Active Client | 4h response | _(add your Tier 2 clients)_ |
| 3 | Prospect | 24h response | _(add your Tier 3 prospects)_ |
| 4 | General | 72h response | Cold outreach, new contacts |

> Full contact list is in `Company_Handbook.md` Section 8.

---

*Last updated by human — 2026-03-11*
*Next review due: 2026-03-18 (weekly)*
