"""
health_monitor.py — Cloud VM Health Monitor for Platinum tier.

Runs on the AWS EC2 VM alongside cloud_orchestrator.py.
Managed by PM2 as a separate process: pm2 start health_monitor.py

Responsibilities:
  1. Write Updates/heartbeat.md every 5 minutes so Local Agent knows Cloud is alive
  2. Check PM2 process list — alert if cloud-agent is not 'online'
  3. Check disk space — alert if < 500 MB free
  4. Git push heartbeat updates periodically so Local can pull them

Usage:
    python3 health_monitor.py
    python3 health_monitor.py --vault /path/to/platinum --interval 300
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Vault root is platinum/ directory
VAULT = Path(__file__).parent.resolve()
load_dotenv(VAULT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [health-monitor] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("health_monitor")

UPDATES_DIR    = VAULT / "Updates"
HEARTBEAT_FILE = UPDATES_DIR / "heartbeat.md"
ALERTS_FILE    = UPDATES_DIR / "alerts.md"
STATUS_FILE    = UPDATES_DIR / "cloud_health.md"
CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "300"))  # 5 min default
DISK_MIN_MB    = 500


def write_heartbeat() -> None:
    """Write/overwrite the heartbeat file with current UTC timestamp."""
    UPDATES_DIR.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_FILE.write_text(
        f"cloud_agent_heartbeat: {datetime.now(timezone.utc).isoformat()}\n",
        encoding="utf-8",
    )
    log.info("Heartbeat written: %s", datetime.now(timezone.utc).isoformat())


def check_pm2() -> dict:
    """Check PM2 process list for cloud-agent status."""
    try:
        result = subprocess.run(
            ["pm2", "jlist"], capture_output=True, text=True, timeout=10
        )
        processes = json.loads(result.stdout)
        for p in processes:
            if p.get("name") == "cloud-agent":
                status     = p.get("pm2_env", {}).get("status", "unknown")
                restarts   = p.get("pm2_env", {}).get("unstable_restarts", 0)
                return {"status": status, "restarts": restarts, "found": True}
        return {"status": "not_found", "restarts": 0, "found": False}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        log.warning("PM2 check failed: %s", e)
        return {"status": "pm2_unavailable", "restarts": 0, "found": False}
    except Exception as e:
        log.error("PM2 check error: %s", e)
        return {"status": "error", "restarts": 0, "found": False}


def check_disk() -> dict:
    """Check free disk space on the vault's filesystem."""
    try:
        usage  = shutil.disk_usage(str(VAULT))
        free_mb = usage.free // (1024 * 1024)
        total_mb = usage.total // (1024 * 1024)
        return {"free_mb": free_mb, "total_mb": total_mb, "ok": free_mb >= DISK_MIN_MB}
    except Exception as e:
        log.warning("Disk check failed: %s", e)
        return {"free_mb": -1, "total_mb": -1, "ok": True}


def check_odoo() -> str:
    """Check Odoo health by hitting /web/database/selector (no auth required).

    Returns "healthy" if HTTP response < 500, or "unreachable: <error>" on failure.
    Uses verify=False because Odoo runs behind a self-signed certificate.
    """
    odoo_url = os.getenv("ODOO_URL", "https://localhost")
    try:
        resp = httpx.get(
            f"{odoo_url}/web/database/selector",
            timeout=10,
            verify=False,
            follow_redirects=True,
        )
        if resp.status_code < 500:
            return "healthy"
        return f"unhealthy: HTTP {resp.status_code}"
    except Exception as e:
        return f"unreachable: {e}"


def write_status(pm2: dict, disk: dict, odoo: str) -> None:
    """Write a human-readable status summary to Updates/cloud_health.md."""
    now        = datetime.now(timezone.utc).isoformat()
    pm2_icon   = "✅" if pm2["status"] == "online" else "❌"
    disk_icon  = "✅" if disk["ok"] else "⚠️"
    odoo_icon  = "✅" if odoo == "healthy" else "❌"
    overall    = (
        "healthy"
        if pm2["status"] == "online" and disk["ok"] and odoo == "healthy"
        else "degraded"
    )

    content = f"""---
agent: cloud_agent
last_check: {now}
pm2_status: {pm2['status']}
pm2_restarts: {pm2['restarts']}
disk_free_mb: {disk['free_mb']}
odoo_status: {odoo}
overall: {overall}
---

# Cloud Agent Health — {now}

| Check | Status |
|---|---|
| PM2 cloud-agent | {pm2_icon} {pm2['status']} (restarts: {pm2['restarts']}) |
| Disk free | {disk_icon} {disk['free_mb']} MB free of {disk['total_mb']} MB |
| Odoo Community | {odoo_icon} {odoo} |

*Updated every {CHECK_INTERVAL // 60} min by health_monitor.py*
"""
    UPDATES_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(content, encoding="utf-8")


def write_alert(msg: str) -> None:
    """Append an alert entry to Updates/alerts.md."""
    timestamp = datetime.now(timezone.utc).isoformat()
    UPDATES_DIR.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(f"- [{timestamp}] ALERT: {msg}\n")
    log.warning("ALERT written: %s", msg)


def git_push_updates() -> None:
    """Push heartbeat and health files to remote so Local can pull them."""
    vault_root = VAULT.parent
    try:
        subprocess.run(["git", "add", str(UPDATES_DIR)],
                       cwd=str(vault_root), capture_output=True, timeout=10)
        status = subprocess.run(
            ["git", "status", "--porcelain", str(UPDATES_DIR)],
            cwd=str(vault_root), capture_output=True, text=True, timeout=10
        )
        if not status.stdout.strip():
            return  # Nothing to push
        subprocess.run(
            ["git", "commit", "-m", f"[cloud] health: heartbeat {datetime.now(timezone.utc).strftime('%H:%M')}"],
            cwd=str(vault_root), capture_output=True, timeout=20
        )
        subprocess.run(["git", "push"], cwd=str(vault_root), capture_output=True, timeout=60)
        log.info("Heartbeat pushed to remote")
    except Exception as e:
        log.warning("git push for heartbeat failed: %s", e)


def run(interval: int = CHECK_INTERVAL) -> None:
    """Main monitoring loop."""
    log.info("Health monitor started | interval=%ds | vault=%s", interval, VAULT)
    UPDATES_DIR.mkdir(parents=True, exist_ok=True)

    push_counter = 0  # push every 3rd check (15 min) to avoid git spam

    while True:
        try:
            # 1. Write heartbeat
            write_heartbeat()

            # 2. Check PM2, disk, Odoo
            pm2  = check_pm2()
            disk = check_disk()
            odoo = check_odoo()

            # 3. Write status summary
            write_status(pm2, disk, odoo)

            # 4. Alert on problems
            if pm2["status"] not in ("online", "pm2_unavailable"):
                write_alert(f"cloud-agent PM2 status is '{pm2['status']}'")
            if pm2["restarts"] > 5:
                write_alert(f"cloud-agent has restarted {pm2['restarts']} times (unstable)")
            if not disk["ok"]:
                write_alert(f"Low disk space: {disk['free_mb']} MB free")
            if odoo != "healthy":
                write_alert(f"Odoo health check failed: {odoo}")

            # 5. Git push every 3rd iteration (every 15 min)
            push_counter += 1
            if push_counter >= 3:
                git_push_updates()
                push_counter = 0

        except Exception as e:
            log.error("Health check error: %s", e, exc_info=True)

        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Platinum Cloud VM Health Monitor")
    parser.add_argument("--vault",    default=str(VAULT), help="Platinum vault path")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL,
                        help="Seconds between checks (default: 300)")
    args = parser.parse_args()
    load_dotenv(Path(args.vault) / ".env")
    run(args.interval)
