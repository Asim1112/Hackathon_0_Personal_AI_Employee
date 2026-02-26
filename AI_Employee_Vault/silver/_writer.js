const fs = require('fs');
const vault = 'F:/Hackathon 0 Personal AI Employee/AI_Employee_Vault/silver';
const BT = String.fromCharCode(96);
const TBT = BT+BT+BT;
const em = '—';
const arr = '→';
const ndash = '–';
const warn = '⚠️';
const phone = '📱';
const red = '🔴';
const yel = '🟡';
const clk = '⏰';
const bar = '━';
const BARS = bar.repeat(38);
const lq = '“';
const rq = '”';
const lsq = '‘';
const rsq = '’';

const lines = [
'---',
'skill: whatsapp_triage',
'version: 1.0',
'tier: silver',
'trigger: called by SKILL_Process_Needs_Action when type: whatsapp is found in Needs_Action/',
'inputs:',
'  - Needs_Action/*.md  where type: whatsapp and status: pending',
'outputs:',
'  - Inbox/DRAFT_WA_REPLY_*.md        (known contacts ' + em + ' awaiting human approval before send)',
'  - Pending_Approval/NEW_CONTACT_REVIEW_*.md  (new contacts ' + em + ' HITL required)',
'  - Pending_Approval/COMPLAINT_REVIEW_*.md    (complaints ' + em + ' never handle autonomously)',
'  - Triage notes written into each source file',
'reads:',
'  - Needs_Action/*.md  (type: whatsapp)',
'  - Company_Handbook.md  (Section 1 WhatsApp rules, Section 4 HITL, Section 11 Key Contacts)',
'  - Dashboard.md',
'writes:',
'  - Needs_Action/*.md  (triage notes + status update in-place)',
'  - Inbox/DRAFT_WA_REPLY_*.md',
'  - Pending_Approval/*.md  (HITL escalations)',
'  - Dashboard.md  (Pending Messages table)',
'called_by: SKILL_Process_Needs_Action',
'calls: SKILL_HITL_Approval  (new contacts, complaints, time-gated)',
'created: 2026-02-25',
'---',
'',
'# SKILL: WhatsApp Triage (Silver Tier)',