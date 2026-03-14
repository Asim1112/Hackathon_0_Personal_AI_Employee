/**
 * odoo-client.js — Odoo JSON-RPC Client
 *
 * Thin wrapper around Odoo's external JSON-RPC API.
 * Docs: https://www.odoo.com/documentation/18.0/developer/reference/external_api.html
 *
 * All methods use the standard /jsonrpc endpoint with the 'object' service.
 * Requires Node 18+ (uses native fetch).
 */

'use strict';

class OdooClient {
  /**
   * @param {object} opts
   * @param {string} opts.url       - Odoo base URL, e.g. http://localhost:8069
   * @param {string} opts.db        - Database name, e.g. ai_employee
   * @param {string} opts.username  - Odoo login email
   * @param {string} opts.password  - Odoo login password
   */
  constructor({ url, db, username, password }) {
    this.url      = url.replace(/\/$/, '');
    this.db       = db;
    this.username = username;
    this.password = password;
    this.uid      = null;
  }

  // ── Core JSON-RPC ────────────────────────────────────────────────────────────

  async _rpc(service, method, args) {
    const res = await fetch(`${this.url}/jsonrpc`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        jsonrpc: '2.0',
        method:  'call',
        id:      Date.now(),
        params:  { service, method, args },
      }),
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status} from Odoo at ${this.url}`);
    }

    const json = await res.json();

    if (json.error) {
      const msg = json.error?.data?.message
               || json.error?.message
               || JSON.stringify(json.error);
      throw new Error(`Odoo RPC error: ${msg}`);
    }

    return json.result;
  }

  // ── Authentication ───────────────────────────────────────────────────────────

  /**
   * Authenticate and cache uid.
   * Called automatically before the first model call.
   */
  async authenticate() {
    this.uid = await this._rpc('common', 'authenticate', [
      this.db, this.username, this.password, {},
    ]);
    if (!this.uid) {
      throw new Error('Odoo authentication failed — check ODOO_USERNAME and ODOO_PASSWORD');
    }
    return this.uid;
  }

  // ── Model Helpers ────────────────────────────────────────────────────────────

  /** Execute any model method (execute_kw) */
  async execute(model, method, args = [], kwargs = {}) {
    if (!this.uid) await this.authenticate();
    return this._rpc('object', 'execute_kw', [
      this.db, this.uid, this.password,
      model, method, args, kwargs,
    ]);
  }

  /** search_read shorthand */
  async searchRead(model, domain = [], fields = [], { limit = 80, order = '' } = {}) {
    return this.execute(model, 'search_read', [domain], { fields, limit, order });
  }

  /** create shorthand — returns new record id */
  async create(model, values) {
    return this.execute(model, 'create', [values]);
  }

  /** write shorthand — returns true */
  async write(model, ids, values) {
    return this.execute(model, 'write', [ids, values]);
  }

  // ── Partner helpers ──────────────────────────────────────────────────────────

  /**
   * Find a partner by exact name, or create one if not found.
   * Returns the partner id.
   */
  async getOrCreatePartner(name, email = null) {
    const found = await this.searchRead(
      'res.partner',
      [['name', '=', name]],
      ['id', 'name', 'email'],
      { limit: 1 },
    );
    if (found.length > 0) return found[0].id;

    const vals = { name, is_company: true };
    if (email) vals.email = email;
    return this.create('res.partner', vals);
  }

  // ── Invoice actions ──────────────────────────────────────────────────────────

  /**
   * Create a draft customer invoice (state: draft).
   * Returns the new invoice id.
   *
   * @param {object} opts
   * @param {string}   opts.partnerName    - Customer name (looked up or created)
   * @param {string}   [opts.partnerEmail] - Customer email (used only if creating partner)
   * @param {Array}    opts.lines          - [{name, quantity, price_unit}]
   * @param {string}   [opts.invoiceDate]  - YYYY-MM-DD  (defaults to today in Odoo)
   * @param {string}   [opts.invoiceDateDue] - YYYY-MM-DD payment due date
   * @param {string}   [opts.ref]          - Customer PO reference
   */
  async createInvoiceDraft({ partnerName, partnerEmail, lines, invoiceDate, invoiceDateDue, ref }) {
    const partnerId = await this.getOrCreatePartner(partnerName, partnerEmail);

    // Odoo expects invoice lines as [(0, 0, {fields})] — one-many write syntax
    const invoiceLineIds = lines.map(l => [0, 0, {
      name:       l.name,
      quantity:   l.quantity    || 1,
      price_unit: l.price_unit  || 0,
    }]);

    const vals = {
      move_type:        'out_invoice',
      partner_id:       partnerId,
      invoice_line_ids: invoiceLineIds,
    };
    if (invoiceDate)    vals.invoice_date     = invoiceDate;
    if (invoiceDateDue) vals.invoice_date_due = invoiceDateDue;
    if (ref)            vals.ref              = ref;

    return this.create('account.move', vals);
  }

  /**
   * Confirm (post) a draft invoice — creates journal entries and assigns invoice number.
   * This is a significant accounting action; always requires prior human approval.
   */
  async confirmInvoice(invoiceId) {
    return this.execute('account.move', 'action_post', [[invoiceId]]);
  }

  // ── Accounting queries ───────────────────────────────────────────────────────

  /**
   * Get all posted customer invoices for a given month.
   * Returns array of invoice records.
   */
  async getMonthlyInvoices(year, month) {
    const m         = String(month).padStart(2, '0');
    const startDate = `${year}-${m}-01`;
    // last day of month
    const endDate   = new Date(year, month, 0).toISOString().split('T')[0];

    return this.searchRead(
      'account.move',
      [
        ['move_type', '=', 'out_invoice'],
        ['state',     '=', 'posted'],
        ['invoice_date', '>=', startDate],
        ['invoice_date', '<=', endDate],
      ],
      ['name', 'partner_id', 'amount_total', 'amount_residual', 'payment_state', 'invoice_date', 'invoice_date_due'],
      { order: 'invoice_date desc' },
    );
  }

  /**
   * Get all overdue customer invoices (posted, unpaid, past due date).
   * Used by odoo_watcher.py to generate Needs_Action/ alerts.
   */
  async getOverdueInvoices() {
    const today = new Date().toISOString().split('T')[0];
    return this.searchRead(
      'account.move',
      [
        ['move_type',     '=',      'out_invoice'],
        ['state',         '=',      'posted'],
        ['payment_state', 'not in', ['paid', 'reversed', 'in_payment']],
        ['invoice_date_due', '<', today],
      ],
      ['name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date_due', 'payment_state'],
      { order: 'invoice_date_due asc' },
    );
  }

  /**
   * Get total posted revenue for a month.
   * Returns { invoiceCount, totalRevenue, collected, outstanding }.
   */
  async getMonthlySummary(year, month) {
    const invoices = await this.getMonthlyInvoices(year, month);
    const totalRevenue  = invoices.reduce((s, i) => s + i.amount_total,    0);
    const outstanding   = invoices.reduce((s, i) => s + i.amount_residual, 0);
    const collected     = totalRevenue - outstanding;
    return {
      invoiceCount: invoices.length,
      totalRevenue:  Math.round(totalRevenue  * 100) / 100,
      collected:     Math.round(collected     * 100) / 100,
      outstanding:   Math.round(outstanding   * 100) / 100,
      invoices,
    };
  }

  /**
   * Ping Odoo — returns server version string or throws.
   */
  async ping() {
    const info = await this._rpc('common', 'version', []);
    return info?.server_version || 'unknown';
  }
}

module.exports = OdooClient;
