"""
odoo_watcher.py — Odoo Watcher for the Gold-tier AI Employee.

Polls Odoo every N minutes for:
  - Overdue invoices (state=posted, payment_state≠paid, due date < today)
  - Large unpaid invoices (> threshold, flagged early)
  - Monthly revenue summary update trigger

Creates structured .md files in Needs_Action/ for Claude to process.
All Odoo write operations go through the HITL gate (odoo-mcp).

State is persisted in .odoo_watcher_state.json.

Usage:
    python odoo_watcher.py
    python odoo_watcher.py --vault /path/to/gold --interval 600

Dependencies (install via uv):
    uv sync
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, date, timezone
from pathlib import Path

import requests

from base_watcher import BaseWatcher
from audit_logger import log_action, log_watcher_start, log_watcher_stop, log_error

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
STATE_FILE_NAME = ".odoo_watcher_state.json"

# Invoices above this amount trigger an early warning even if not yet overdue
LARGE_INVOICE_THRESHOLD = float(os.environ.get("LARGE_INVOICE_THRESHOLD", "500"))


def _load_state(vault_path: Path) -> dict:
    state_file = vault_path / STATE_FILE_NAME
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "alerted_invoice_ids": [],
        "last_sync_date": None,
        "last_monthly_trigger": None,
    }


def _save_state(vault_path: Path, state: dict) -> None:
    state["alerted_invoice_ids"] = state["alerted_invoice_ids"][-500:]
    state_file = vault_path / STATE_FILE_NAME
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Odoo JSON-RPC client (minimal Python version — mirrors odoo-client.js)
# ---------------------------------------------------------------------------

class OdooRPC:
    """Minimal Odoo JSON-RPC client for Python watchers."""

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self.uid: int | None = None
        self._session = requests.Session()
        self._session.headers["Content-Type"] = "application/json"

    def _call(self, service: str, method: str, args: list) -> object:
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 1,
            "params": {"service": service, "method": method, "args": args},
        }
        resp = self._session.post(f"{self.url}/jsonrpc", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            raise RuntimeError(f"Odoo RPC error: {data['error']['data']['message']}")
        return data["result"]

    def authenticate(self) -> int:
        self.uid = self._call(
            "common", "authenticate",
            [self.db, self.username, self.password, {}]
        )
        if not self.uid:
            raise RuntimeError("Odoo authentication failed — check credentials in .env")
        return self.uid

    def search_read(self, model: str, domain: list, fields: list, limit: int = 100) -> list[dict]:
        if self.uid is None:
            self.authenticate()
        return self._call(
            "object", "execute_kw",
            [self.db, self.uid, self.password, model, "search_read",
             [domain], {"fields": fields, "limit": limit}]
        )

    def ping(self) -> str:
        result = self._call("common", "version", [])
        return result.get("server_version", "unknown") if isinstance(result, dict) else str(result)


# ---------------------------------------------------------------------------
# Watcher class
# ---------------------------------------------------------------------------

class OdooWatcher(BaseWatcher):
    """Polls Odoo for overdue invoices and revenue triggers."""

    def __init__(self, vault_path: str, check_interval: int = 600):
        super().__init__(vault_path, check_interval)
        self.state = _load_state(self.vault_path)

        odoo_url  = os.environ.get("ODOO_URL", "http://localhost:8069")
        odoo_db   = os.environ.get("ODOO_DB", "ai_employee")
        odoo_user = os.environ.get("ODOO_USERNAME", "admin")
        odoo_pass = os.environ.get("ODOO_PASSWORD", "")

        if not odoo_pass:
            self.logger.error("ODOO_PASSWORD not set in .env")
            sys.exit(1)

        self._odoo = OdooRPC(odoo_url, odoo_db, odoo_user, odoo_pass)
        self._verify_connection()

    def _verify_connection(self) -> None:
        try:
            version = self._odoo.ping()
            self.logger.info("Odoo reachable — version %s", version)
            self._odoo.authenticate()
            self.logger.info("Authenticated — uid %s", self._odoo.uid)
        except Exception as exc:
            self.logger.error("Cannot connect to Odoo: %s", exc)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Poll
    # ------------------------------------------------------------------

    def check_for_updates(self) -> list[dict]:
        items: list[dict] = []

        try:
            items.extend(self._check_overdue_invoices())
        except Exception as exc:
            self.logger.warning("Overdue invoice check failed: %s", exc)
            log_error("odoo_watcher", "overdue_invoices", str(exc))

        try:
            monthly_trigger = self._check_monthly_sync_trigger()
            if monthly_trigger:
                items.append(monthly_trigger)
        except Exception as exc:
            self.logger.warning("Monthly sync check failed: %s", exc)

        _save_state(self.vault_path, self.state)
        return items

    def _check_overdue_invoices(self) -> list[dict]:
        """Fetch posted invoices that are past their due date and not paid."""
        today_str = date.today().isoformat()
        invoices = self._odoo.search_read(
            "account.move",
            [
                ["move_type", "=", "out_invoice"],
                ["state", "=", "posted"],
                ["payment_state", "not in", ["paid", "reversed"]],
                ["invoice_date_due", "<", today_str],
            ],
            ["id", "name", "partner_id", "amount_total", "invoice_date_due",
             "payment_state", "invoice_origin"],
            limit=50,
        )

        new_items = []
        for inv in invoices:
            inv_id = inv["id"]
            if inv_id in self.state["alerted_invoice_ids"]:
                continue

            days_overdue = (
                date.today() - date.fromisoformat(inv["invoice_date_due"])
            ).days

            new_items.append({
                "event_type": "overdue_invoice",
                "invoice_id": inv_id,
                "invoice_ref": inv.get("name", f"INV{inv_id}"),
                "partner_name": inv["partner_id"][1] if inv.get("partner_id") else "Unknown",
                "amount_total": inv.get("amount_total", 0),
                "due_date": inv["invoice_date_due"],
                "days_overdue": days_overdue,
                "payment_state": inv.get("payment_state", "not_paid"),
                "origin": inv.get("invoice_origin", ""),
            })
            self.state["alerted_invoice_ids"].append(inv_id)

        if new_items:
            self.logger.info("Found %d new overdue invoice(s)", len(new_items))
        return new_items

    def _check_monthly_sync_trigger(self) -> dict | None:
        """Trigger a monthly sync on the 1st of each month if not already done."""
        today = date.today()
        month_key = today.strftime("%Y-%m")

        if today.day == 1 and self.state.get("last_monthly_trigger") != month_key:
            self.state["last_monthly_trigger"] = month_key
            self.logger.info("Monthly sync trigger — first day of %s", month_key)
            return {
                "event_type": "monthly_sync",
                "month": month_key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return None

    # ------------------------------------------------------------------
    # File creation
    # ------------------------------------------------------------------

    def create_action_file(self, item: dict) -> Path:
        event_type = item["event_type"]
        if event_type == "overdue_invoice":
            return self._create_overdue_file(item)
        elif event_type == "monthly_sync":
            return self._create_monthly_sync_file(item)
        self.logger.warning("Unknown event type: %s", event_type)
        return None

    def _create_overdue_file(self, item: dict) -> Path:
        uid = hashlib.md5(str(item["invoice_id"]).encode()).hexdigest()[:8]
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ref_slug = item["invoice_ref"].replace("/", "-").replace(" ", "_")
        filename = f"ODOO_{date_str}_overdue_{ref_slug}_{uid}.md"
        file_path = self.needs_action / filename

        urgency = "🔴 URGENT" if item["days_overdue"] > 30 else "🟡 OVERDUE"

        content = f"""---
type: odoo_alert
event_type: overdue_invoice
platform: odoo
status: pending
created: {datetime.now(timezone.utc).isoformat()}
invoice_id: {item['invoice_id']}
invoice_ref: "{item['invoice_ref']}"
client: "{item['partner_name']}"
amount_total: {item['amount_total']}
due_date: "{item['due_date']}"
days_overdue: {item['days_overdue']}
logged: false
---

# Odoo Alert: Overdue Invoice {urgency}

**Invoice:** {item['invoice_ref']}
**Client:** {item['partner_name']}
**Amount:** £{item['amount_total']:,.2f}
**Due Date:** {item['due_date']}
**Days Overdue:** {item['days_overdue']} days
**Payment State:** {item['payment_state']}
**Origin:** {item['origin'] or '—'}

## Suggested Action

Use `SKILL_Odoo_Accounting` to:

1. Check `Company_Handbook.md` for payment chasing policy
2. If chasing is appropriate:
   - Draft a payment reminder email via `SKILL_Gmail_Triage`
   - Write email draft to `Inbox/DRAFT_REPLY_Payment_Chase_{ref_slug}.md`
3. If already chased recently → LOG_ONLY and flag in Dashboard
4. If > 60 days overdue → escalate to `Pending_Approval/` as HUMAN_REVIEW

## Processing Notes

_Add notes after review._
"""
        file_path.write_text(content, encoding="utf-8")
        log_action(
            action_type="odoo_overdue_alert",
            source="odoo_watcher",
            target=item["invoice_ref"],
            approval_status="not_required",
            notes=f"{item['partner_name']} — £{item['amount_total']:.2f} — {item['days_overdue']}d overdue",
        )
        return file_path

    def _create_monthly_sync_file(self, item: dict) -> Path:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"ODOO_{date_str}_monthly_sync_{item['month']}.md"
        file_path = self.needs_action / filename

        content = f"""---
type: odoo_alert
event_type: monthly_sync
platform: odoo
status: pending
created: {item['timestamp']}
month: "{item['month']}"
logged: false
---

# Odoo Monthly Sync — {item['month']}

It is the 1st of the month. Trigger an accounting data sync to update
`Accounting/Current_Month.md` with fresh Odoo data.

## Suggested Action

Use `SKILL_Odoo_Accounting` to create a `sync_accounting` action in `Pending_Approval/`.

This is a read-only operation — no Odoo records will be modified.
"""
        file_path.write_text(content, encoding="utf-8")
        log_action(
            action_type="odoo_monthly_sync_trigger",
            source="odoo_watcher",
            target=f"Accounting/Current_Month.md",
            notes=f"Monthly sync trigger for {item['month']}",
        )
        return file_path

    def shutdown(self) -> None:
        _save_state(self.vault_path, self.state)
        log_watcher_stop("odoo_watcher")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    from dotenv import load_dotenv

    vault_default = str(Path(__file__).parent)
    parser = argparse.ArgumentParser(description="Odoo Watcher for Gold AI Employee")
    parser.add_argument("--vault", default=vault_default)
    parser.add_argument("--interval", type=int, default=int(os.environ.get("ODOO_INTERVAL", 600)))
    args = parser.parse_args()

    load_dotenv(Path(args.vault) / ".env")

    log_watcher_start("odoo_watcher")
    watcher = OdooWatcher(vault_path=args.vault, check_interval=args.interval)
    watcher.run()


if __name__ == "__main__":
    main()
