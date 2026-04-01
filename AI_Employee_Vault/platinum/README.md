# Platinum Tier — Personal AI Employee

**Tier: Platinum**
**Repository:** https://github.com/Asim1112/Hackathon_0_Personal_AI_Employee
**Vault path:** `AI_Employee_Vault/platinum/`

---

## Architecture Overview

Platinum introduces a **two-agent split**: a always-on Cloud Agent (AWS EC2) handles triage and drafting; a Local Agent (Windows) handles approvals and execution via MCP servers.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLOUD AGENT (AWS EC2)                        │
│                                                                     │
│  Gmail Watcher ──► Needs_Action/email/  ──► Cloud Reasoning         │
│  Social Watcher ─► Needs_Action/social/ ──► (CLOUD_CLAUDE.md)       │
│                                              │                      │
│              Pending_Approval/email/  ◄──────┘                      │
│              Pending_Approval/social/ ◄──── draft_reply             │
│                    │                        odoo_action             │
│              Updates/ (heartbeat, health)                           │
│                    │                                                │
│              git push ──────────────────────────────────────────►   │
└─────────────────────────────────────────────────────────────────────┘
                              │ GitHub
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LOCAL AGENT (Windows)                          │
│                                                                     │
│  git pull ──► Pending_Approval/  ──► Human Reviews                  │
│                                        │                            │
│                                   mv to Approved/                   │
│                                        │                            │
│              ┌─────────────────────────┼──────────────────────┐     │
│              │         MCP Servers (Node.js, always watching)  │     │
│              │  email-mcp ──────────► Send email via SMTP      │     │
│              │  odoo-mcp  ──────────► Create Odoo invoice      │     │
│              └──────────────────────────────────────────────── ┘     │
│                                        │                            │
│                                     Done/ + Logs/                   │
│                    WhatsApp Watcher ──► Needs_Action/email/          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Two-Agent Split

| Domain | Cloud Agent (AWS EC2) | Local Agent (Windows) |
|---|---|---|
| Email triage | Reads `Needs_Action/email/`, drafts replies | Reviews `Pending_Approval/email/`, approves |
| Social drafts | Reads `Needs_Action/social/`, writes drafts | Reviews `Pending_Approval/social/`, approves |
| Odoo actions | Writes `odoo_action` draft to `Pending_Approval/` | Approves → odoo-mcp executes |
| WhatsApp | — | Owns `whatsapp_session/`, writes to `Needs_Action/email/` |
| Email sending | — | email-mcp sends via SMTP after `Approved/` move |
| Dashboard.md | — | Sole writer |
| Heartbeat | Writes `Updates/heartbeat.md` every 5 min | Monitors staleness |
| Odoo health | `health_monitor.py` checks `/web/database/selector` | — |
| git push | After every triage cycle | After every approval cycle |

---

## Folder Structure

```
platinum/
├── Needs_Action/
│   ├── email/          ← Gmail + WhatsApp items land here
│   └── social/         ← LinkedIn/Twitter/Facebook items
├── In_Progress/
│   ├── cloud_agent/    ← Cloud claims (claim-by-move rule)
│   └── local_agent/    ← Local claims
├── Pending_Approval/
│   ├── email/          ← draft_reply, approval_request, odoo_action files
│   └── social/         ← social_draft files
├── Approved/           ← Human moves files here → MCP servers execute
├── Done/               ← Completed files (never deleted)
├── Logs/               ← YYYY-MM-DD.json audit trail (one file per day)
├── Updates/            ← heartbeat.md, cloud_health.md, cloud_status.md
├── docker/odoo/        ← docker-compose.yml, nginx.conf, backup.sh
├── mcp_servers/
│   ├── email-mcp/      ← Node.js SMTP sender, watches Approved/
│   └── odoo-mcp/       ← Node.js Odoo client, watches Approved/
├── cloud_orchestrator.py
├── health_monitor.py
├── local_orchestrator.py
├── email_sender.py
├── whatsapp_watcher.py
├── gmail_watcher.py
├── base_watcher.py
├── CLOUD_CLAUDE.md     ← Cloud Agent operating instructions
├── LOCAL_CLAUDE.md     ← Local Agent operating instructions
└── pyproject.toml
```

---

## Cloud VM Setup (AWS EC2)

### Prerequisites
- AWS EC2 t2.micro, Ubuntu 22.04 LTS
- Security group inbound rules: SSH (22), HTTP (80), HTTPS (443)
- SSH key pair saved as `~/.ssh/ai-employee-key.pem`

### Step 1 — Connect and update
```bash
ssh -i ~/.ssh/ai-employee-key.pem ubuntu@100.48.121.225
sudo apt update && sudo apt upgrade -y
```

### Step 2 — Add 2GB swap (required for Odoo on t2.micro)
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Step 3 — Install Python 3.13 + uv
```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install -y python3.13 python3.13-venv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### Step 4 — Install Node.js 20 + PM2
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2
pm2 startup
```

### Step 5 — Install Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker
```

### Step 6 — Clone repository and install dependencies
```bash
cd ~
git clone https://github.com/Asim1112/Hackathon_0_Personal_AI_Employee.git
cd Hackathon_0_Personal_AI_Employee/AI_Employee_Vault/platinum
uv sync
```

### Step 7 — Configure .env on VM
```bash
cp .env.example .env   # if available, or create manually
# Add to .env:
# AGENT_ID=cloud_agent
# GMAIL_ADDRESS=your-gmail@gmail.com
# ODOO_URL=https://100.48.121.225
# ODOO_DB=ai_employee
# ODOO_USERNAME=admin
# ODOO_PASSWORD=admin
# ODOO_DB_PASSWORD=OdooSecure2026
```

### Step 8 — Deploy Odoo Community 17
```bash
cd ~/Hackathon_0_Personal_AI_Employee/AI_Employee_Vault/platinum/docker/odoo

# Generate self-signed SSL certificate
VM_IP=$(curl -s ifconfig.me)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/odoo.key -out certs/odoo.crt \
  -subj "/CN=${VM_IP}/O=AI Employee/C=GB" \
  -addext "subjectAltName=IP:${VM_IP}"

# Start the stack (PostgreSQL 16 + Odoo 17 + Nginx)
ODOO_DB_PASSWORD=OdooSecure2026 docker compose up -d
docker compose ps   # verify: db, odoo, nginx all "Up"
```

Then open `https://100.48.121.225` in a browser, accept the SSL warning, and
initialize the `ai_employee` database (Master Password: `OdooSecure2026`).

### Step 9 — Start agents with PM2
```bash
cd ~/Hackathon_0_Personal_AI_Employee/AI_Employee_Vault/platinum
pm2 start cloud_orchestrator.py --name cloud-agent --interpreter uv -- run python
pm2 start health_monitor.py     --name health-monitor --interpreter uv -- run python
pm2 save
pm2 status   # both should show "online"
```

### Step 10 — Set up daily backup cron
```bash
BACKUP_SCRIPT="$HOME/Hackathon_0_Personal_AI_Employee/AI_Employee_Vault/platinum/docker/odoo/backup.sh"
chmod +x "$BACKUP_SCRIPT"
(crontab -l 2>/dev/null; echo "0 2 * * * $BACKUP_SCRIPT >> $HOME/odoo_backup.log 2>&1") | crontab -
```

---

## Local Machine Setup (Windows)

### Prerequisites
- Windows 10/11
- Python 3.13+ and [uv](https://astral.sh/uv) installed
- Node.js 20+ installed
- Claude Code CLI: `npm install -g @anthropic/claude-code`
- Git configured with SSH access to the repository

### Step 1 — Clone repository
```bash
git clone https://github.com/Asim1112/Hackathon_0_Personal_AI_Employee.git
cd "Hackathon_0_Personal_AI_Employee/AI_Employee_Vault/platinum"
```

### Step 2 — Install Python dependencies
```bash
uv sync
```

### Step 3 — Configure local .env
Create `platinum/.env` (gitignored — never committed):
```env
AGENT_ID=local_agent
GMAIL_ADDRESS=your-gmail@gmail.com
ODOO_URL=https://100.48.121.225
ODOO_DB=ai_employee
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

### Step 4 — Configure email-mcp credentials
Create `platinum/mcp_servers/email-mcp/mcp.json` (gitignored):
```json
{
  "smtp_host":   "smtp.gmail.com",
  "smtp_port":   587,
  "smtp_secure": false,
  "smtp_user":   "your-gmail@gmail.com",
  "smtp_pass":   "your-16-char-app-password",
  "from":        "Your Name <your-gmail@gmail.com>",
  "vault_path":  "../..",
  "dry_run":     false
}
```
Obtain a Gmail App Password at: Google Account → Security → 2-Step Verification → App passwords.

### Step 5 — Install MCP server dependencies
```bash
cd platinum/mcp_servers/email-mcp && npm install
cd ../odoo-mcp && npm install
```

### Step 6 — (Optional) WhatsApp setup
First-run only — scan QR code to authenticate:
```bash
cd platinum
uv run python whatsapp_watcher.py --no-headless
# Scan QR code in the browser window, then Ctrl-C
# Session saved to whatsapp_session/ — subsequent runs are headless
```

---

## How to Run

### Cloud VM (both processes via PM2 — already running after setup)
```bash
# Check status
pm2 status

# View live logs
pm2 logs cloud-agent --lines 50
pm2 logs health-monitor --lines 20

# Force immediate triage cycle (bypasses schedule)
cd ~/Hackathon_0_Personal_AI_Employee/AI_Employee_Vault/platinum
uv run python cloud_orchestrator.py --cron

# Restart if needed
pm2 restart cloud-agent
pm2 restart health-monitor
```

### Local Machine (Windows) — Terminal 1: email-mcp
```bash
cd "AI_Employee_Vault/platinum/mcp_servers/email-mcp"
node index.js
# Keep this terminal open — it watches Approved/ continuously
```

### Local Machine — Terminal 2: local_orchestrator
```bash
cd "AI_Employee_Vault/platinum"

# Daemon mode (auto-pull every 5 min + daily Claude cycle at 08:00)
uv run python local_orchestrator.py

# Pull-only (check for new Cloud Agent drafts and exit)
uv run python local_orchestrator.py --pull

# Immediate Claude cycle (process all pending approvals now)
uv run python local_orchestrator.py --now
```

### Local Machine — Terminal 3: odoo-mcp (when Odoo tasks are pending)
```bash
cd "AI_Employee_Vault/platinum/mcp_servers/odoo-mcp"
node index.js
```

---

## Minimum Passing Gate — Demo Instructions

This validates the full end-to-end flow: **Email arrives → Cloud drafts reply → Local approves → MCP sends → Logs → Done**

### Step 1 — Drop a test email into the queue
Create a file `platinum/Needs_Action/email/EMAIL_<date>_<subject>_<id>.md`:
```yaml
---
type: email
platform: gmail
from: reviewer@example.com
subject: Quick Project Status Update
received: <ISO timestamp>
message_id: demo-001
status: pending
priority: medium
---

Hi, could you send me a project status update? Thanks.
```

Commit and push so the Cloud Agent can see it:
```bash
git add platinum/Needs_Action/email/
git commit -m "[local] demo: add test email"
git push
```

### Step 2 — Trigger the Cloud Agent
```bash
ssh -i ~/.ssh/ai-employee-key.pem ubuntu@100.48.121.225
cd ~/Hackathon_0_Personal_AI_Employee/AI_Employee_Vault/platinum
uv run python cloud_orchestrator.py --cron
```

The Cloud Agent will:
- `git pull` to receive the new email
- Triage it and write a `draft_reply` to `Pending_Approval/email/`
- Commit and push

### Step 3 — Pull and review the draft
```bash
# On Windows:
git pull
cat "platinum/Pending_Approval/email/DRAFT_REPLY_*.md"
```

Verify it contains `type: draft_reply`, `send_via_mcp: email-mcp`, and `to: <recipient>`.

### Step 4 — Start email-mcp (Terminal 1)
```bash
cd platinum/mcp_servers/email-mcp
node index.js
# Should print: Watching /Approved — waiting for approved email drafts…
```

### Step 5 — Approve (move to Approved/)
```bash
mv "platinum/Pending_Approval/email/DRAFT_REPLY_*.md" platinum/Approved/
```

### Step 6 — Verify send
Within 5 seconds, Terminal 1 (email-mcp) should show:
```
[email-mcp] INFO  Sending → To: reviewer@example.com | Subject: Re: Quick Project Status Update
[email-mcp] OK    Sent DRAFT_REPLY_*.md — msgId: <id>
[email-mcp] INFO  → Done/DRAFT_REPLY_*.md
```

Check that the email arrived in the recipient inbox. The file is now in `Done/`.

### Step 7 — Verify audit log
```bash
cd platinum
python -c "
import json; from pathlib import Path
log = json.loads(Path('Logs/$(date +%Y-%m-%d).json').read_text())
print(json.dumps(log[-1], indent=2))
"
```

Confirm all 8 required fields: `timestamp`, `action_type`, `actor`, `target`,
`parameters`, `approval_status`, `approved_by`, `result`.

---

## Security Disclosure

### Credential Storage Policy

All secrets are stored in files that are **gitignored and never committed**:

| File | Contains | Gitignored |
|---|---|---|
| `platinum/.env` | SMTP address, Odoo credentials, agent config | Yes — `*.env` |
| `platinum/mcp_servers/email-mcp/mcp.json` | Gmail App Password (SMTP) | Yes — `mcp.json` |
| `platinum/docker/odoo/certs/odoo.key` | SSL private key | Yes — `*.key` |
| `platinum/docker/odoo/certs/odoo.crt` | SSL certificate | Yes — `*.crt` |
| `whatsapp_session/` | Playwright browser session (WhatsApp auth) | Yes — `whatsapp_session/` |

### What Syncs to Git (markdown and state files only)

- `.md` files: task queue, drafts, approvals, audit entries, dashboard
- `.json` files: daily audit logs in `Logs/`, watcher deduplication state
- Python and Node.js source code
- `docker-compose.yml`, `nginx.conf`, `backup.sh` (no secrets)

### What NEVER Syncs to Git

- `.env` files (all environments)
- `mcp.json` (SMTP App Password)
- `*.pem`, `*.key`, `*.crt` (SSL/SSH keys)
- `whatsapp_session/` (browser auth cookies)
- `credentials.json`, `token.json` (OAuth tokens)
- `node_modules/` (dependencies)
- `__pycache__/`, `.venv/` (build artifacts)

### HITL Guarantee

**Nothing executes without an explicit human approval move.**

The MCP servers (email-mcp, odoo-mcp) watch `Approved/` continuously. They only
execute when a human physically moves a file from `Pending_Approval/<domain>/` to
`Approved/`. The Cloud Agent and Local Agent reasoning loops produce draft files
only — they have no ability to call MCP servers directly.

The claim-by-move rule prevents double-processing: the first agent to move a file
to `In_Progress/<agent>/` owns that task exclusively.

### Audit Trail Location

Every action taken by either agent is appended to:
```
platinum/Logs/YYYY-MM-DD.json
```

Schema (hackathon-compliant, 8 required fields):
```json
{
  "timestamp":       "<ISO 8601 UTC>",
  "action_type":     "<email_send | email_acknowledged | email_triage | ...>",
  "actor":           "<cloud_agent | local_agent>",
  "target":          "<email address | filename | platform>",
  "parameters":      { "subject": "...", "file": "..." },
  "approval_status": "<approved | not_required | pending>",
  "approved_by":     "<human | system>",
  "result":          "<success | skipped | failed | escalated>"
}
```

Logs are committed to git by both agents and are therefore permanently
replicated to GitHub as an immutable audit trail.

---

## Compliance Checklist

| Requirement | Implementation | Status |
|---|---|---|
| Cloud Agent always-on | PM2-managed `cloud_orchestrator.py` on AWS EC2 | ✅ |
| Local Agent approvals | `local_orchestrator.py` + human `Approved/` move | ✅ |
| Email via MCP only | `email-mcp` (Node.js SMTP) is sole email sender | ✅ |
| Draft reply flow | `draft_reply` → `email-mcp` → SMTP send | ✅ |
| Odoo on Cloud VM | Odoo 17 + PostgreSQL 16 + Nginx via Docker at `https://100.48.121.225` | ✅ |
| Odoo MCP integration | `odoo-mcp` handles `odoo_action` files from `Approved/` | ✅ |
| WhatsApp Local Agent | `whatsapp_watcher.py` thread in `local_orchestrator.py` | ✅ |
| Audit log schema | 8-field JSON schema in every log entry | ✅ |
| HITL gate | Nothing executes without `Approved/` move | ✅ |
| Health monitoring | `health_monitor.py` checks PM2 + disk + Odoo, alerts on failure | ✅ |
| Daily backup | `backup.sh` cron at 02:00 UTC, 7-day retention | ✅ |
| Security disclosure | Secrets gitignored, credentials never committed | ✅ |

---

*Platinum Tier — Personal AI Employee — Hackathon 2026*
