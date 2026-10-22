from odoo import _, api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime


class ServiceContract(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'elevata.service.contract'
    _description = 'Service Contract'
    _order = 'id desc'

    name = fields.Char(
        string="Contract Reference",
        required=True,
        readonly=True,
        default='New',
        copy=False,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    contract_years = fields.Integer(
        string="Contract Years",
        required=True,
        default=1,
        tracking=True,
    )
    date_end = fields.Date(
        string="End Date",
        compute='_compute_date_end',
        store=True,
        readonly=True,
        tracking=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ], string="Status", default='draft', tracking=True)

    content = fields.Html(string="Contract Content", sanitize=False)

    line_ids = fields.One2many(
        'elevata.service.contract.line',
        'service_contract_id',
        string="Contract Lines",
    )
    template_modification_ids = fields.One2many(
        'elevata.service.contract.template.modification',
        'service_contract_id',
        string="Template Modifications",
    )
    fsm_order_ids = fields.One2many(
        'fieldservice.order',
        'service_contract_id',
        string="Work Orders",
    )
    fsm_order_count = fields.Integer(
        string="Work Orders",
        compute='_compute_fsm_order_count',
    )
    price_rule_ids = fields.One2many(
        'elevata.contract.price.rule',
        'service_contract_id',
        string="Price Rules",
    )
    pricelist_id = fields.Many2one(
        'elevata.pricelist',
        string="Pricelist",
        ondelete='set null',
        tracking=True,
    )
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string="Payment Terms",
        tracking=True,
    )
    billing_interval = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('manual', 'Manual'),
    ], string="Billing Interval", default='yearly', tracking=True)

    next_invoice_date = fields.Date(
        string="Next Invoice Date",
        tracking=True,
    )
    invoice_ids = fields.One2many(
        'account.move',
        'service_contract_id',
        string="Invoices",
        copy=False,
    )
    invoice_count = fields.Integer(
        string="Invoices",
        compute='_compute_invoice_count',
    )
    amount_total = fields.Float(
        string="Total Annual Amount",
        compute='_compute_amount_total',
        store=True,
    )

    # ── Computed ──

    @api.depends('date_start', 'contract_years')
    def _compute_date_end(self):
        for rec in self:
            if rec.date_start and rec.contract_years:
                rec.date_end = rec.date_start + relativedelta(
                    years=rec.contract_years
                ) - relativedelta(days=1)
            else:
                rec.date_end = False

    def _compute_fsm_order_count(self):
        for rec in self:
            rec.fsm_order_count = len(rec.fsm_order_ids)

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.depends('line_ids.price_unit')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('price_unit'))

    # ── Onchange ──

    @api.onchange('partner_id')
    def _onchange_partner_id_pricelist(self):
        if self.partner_id and self.partner_id.elevata_pricelist_id:
            self.pricelist_id = self.partner_id.elevata_pricelist_id

    # ── Actions ──

    def action_view_fsm_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Orders'),
            'res_model': 'fieldservice.order',
            'view_mode': 'tree,form',
            'domain': [('service_contract_id', '=', self.id)],
            'context': {'default_service_contract_id': self.id},
        }

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('service_contract_id', '=', self.id)],
        }

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(
                    _('Add at least one contract line before confirming.')
                )
            rec._check_location_overlap()
            next_date = (
                rec._get_next_invoice_date()
                if rec.billing_interval != 'manual'
                else False
            )
            rec.write({
                'state': 'confirmed',
                'next_invoice_date': next_date,
            })
            rec._schedule_renewal_reminder()
            prepaid_lines = rec.line_ids.filtered(
                lambda l: l.billing_type == 'prepaid'
            )
            if prepaid_lines:
                rec._create_prepaid_invoice(prepaid_lines)
            rec._generate_orders_for_contract()

    # ── Overlap check ──

    def _check_location_overlap(self):
        for rec in self:
            for line in rec.line_ids:
                if not line.equipment_id:
                    continue
                candidates = self.search([
                    ('id', '!=', rec.id),
                    ('state', '=', 'confirmed'),
                    ('line_ids.equipment_id', '=', line.equipment_id.id),
                ])
                for other in candidates:
                    s1, e1 = rec.date_start, rec.date_end
                    s2, e2 = other.date_start, other.date_end
                    overlap = (
                        (not e1 or not s2 or e1 >= s2)
                        and (not e2 or not s1 or e2 >= s1)
                    )
                    if overlap:
                        raise UserError(
                            _('Elevator "%s" is already covered by active '
                              'contract (%s) during this period.')
                            % (line.equipment_id.complete_name, other.name)
                        )

    # ── Invoice helpers ──

    def _get_next_invoice_date(self, from_date=None):
        self.ensure_one()
        base = from_date or self.date_start or fields.Date.today()
        if self.billing_interval == 'monthly':
            return base + relativedelta(months=1)
        elif self.billing_interval == 'quarterly':
            return base + relativedelta(months=3)
        elif self.billing_interval == 'yearly':
            return base + relativedelta(years=1)
        return False

    def _get_period_amount(self, line):
        if self.billing_interval == 'monthly':
            return line.price_unit / 12.0
        elif self.billing_interval == 'quarterly':
            return line.price_unit / 4.0
        return line.price_unit

    def _create_prepaid_invoice(self, lines):
        self.ensure_one()
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'service_contract_id': self.id,
            'invoice_date': fields.Date.today(),
            'invoice_payment_term_id': (
                self.payment_term_id.id
                or self.partner_id.property_payment_term_id.id
                or False
            ),
            'fiscal_position_id': (
                self.partner_id.property_account_position_id.id or False
            ),
            'invoice_line_ids': [
                (0, 0, {
                    'name': _('Service Contract %s — %s') % (
                        self.name, line.equipment_id.name
                    ),
                    'quantity': 1.0,
                    'price_unit': line.price_unit,
                })
                for line in lines
            ],
        })
        return invoice

    def action_create_invoice(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(
                _('Contract must be confirmed before creating an invoice.')
            )
        prepaid_lines = self.line_ids.filtered(
            lambda l: l.billing_type == 'prepaid'
        )
        if not prepaid_lines:
            raise UserError(
                _('No prepaid lines to invoice. On-demand visits are '
                  'invoiced via work orders.')
            )
        invoice = self._create_prepaid_invoice(prepaid_lines)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }

    def action_invoice_postpaid_lines(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(
                _('Contract must be confirmed before creating an invoice.')
            )
        postpaid_lines = self.line_ids.filtered(
            lambda l: l.billing_type == 'postpaid'
        )
        if not postpaid_lines:
            raise UserError(_('No on-demand lines to invoice.'))
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'service_contract_id': self.id,
            'invoice_date': fields.Date.today(),
            'invoice_payment_term_id': (
                self.payment_term_id.id
                or self.partner_id.property_payment_term_id.id
                or False
            ),
            'fiscal_position_id': (
                self.partner_id.property_account_position_id.id or False
            ),
            'invoice_line_ids': [
                (0, 0, {
                    'name': _('Service Contract %s — %s (%s)') % (
                        self.name,
                        line.equipment_id.name,
                        line.contract_type_selection,
                    ),
                    'quantity': 1.0,
                    'price_unit': line.price_unit,
                })
                for line in postpaid_lines
            ],
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }

    # ── Work order generation ──

    def action_generate_service_orders(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(
                _('Contract must be confirmed before generating work orders.')
            )
        created = self._generate_orders_for_contract()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Work Orders Created'),
                'message': _('%d work orders created.') % created,
                'type': 'success',
            },
        }

    def _generate_orders_for_contract(self):
        created_count = 0
        service_type = self.env.ref(
            'fieldservice_order_type_color.fsm_order_type_service',
            raise_if_not_found=False,
        )
        inspection_type = self.env.ref(
            'fieldservice_order_type_color.fsm_order_type_inspection',
            raise_if_not_found=False,
        )
        for line in self.line_ids:
            if not line.visits_per_year or line.visits_per_year == '0':
                continue
            interval_months = 12 // int(line.visits_per_year)
            current_date = self.date_start
            while current_date <= self.date_end:
                existing = self.env['fieldservice.order'].search_count([
                    ('service_contract_id', '=', self.id),
                    ('equipment_id', '=', line.equipment_id.id),
                    ('planned_start_datetime', '>=',
                     fields.Date.to_string(current_date)),
                    ('planned_start_datetime', '<',
                     fields.Date.to_string(
                         current_date + relativedelta(months=interval_months)
                     )),
                ])
                if not existing:
                    vals = {
                        # fieldservice.order.name is NOT NULL in the Vertel fork
                        # (it is not auto-filled from the sequence).
                        'name': _('Service visit — %s') % (
                            line.equipment_id.name or self.name),
                        'equipment_id': line.equipment_id.id,
                        'service_contract_id': self.id,
                        'planned_start_datetime': datetime.combine(
                            current_date, datetime.min.time()
                        ),
                        'product_tmpl_id': service_type.id if service_type else False,
                        'billing_type': line.billing_type,
                        'elevata_contract_type': line.contract_type_selection,
                    }
                    if (line.customer_id
                            and 'customer_id' in self.env['fieldservice.order']._fields):
                        vals['customer_id'] = line.customer_id.id
                    order = self.env['fieldservice.order'].create(vals)
                    self._generate_checklist_for_order(
                        order, line.equipment_id
                    )
                    created_count += 1
                current_date += relativedelta(months=interval_months)

            if line.include_inspection:
                insp_month = None
                if (line.equipment_id
                        and line.equipment_id.inspection_month):
                    insp_month = int(line.equipment_id.inspection_month)
                if insp_month:
                    insp_date = self.date_start.replace(
                        month=insp_month, day=1
                    )
                    if insp_date < self.date_start:
                        insp_date += relativedelta(years=1)
                else:
                    insp_date = self.date_start + relativedelta(months=11)
                while insp_date <= self.date_end:
                    existing = self.env['fieldservice.order'].search_count([
                        ('service_contract_id', '=', self.id),
                        ('equipment_id', '=', line.equipment_id.id),
                        ('product_tmpl_id', '=',
                         inspection_type.id if inspection_type else False),
                        ('planned_start_datetime', '>=',
                         datetime.combine(insp_date, datetime.min.time())),
                        ('planned_start_datetime', '<',
                         datetime.combine(
                             insp_date + relativedelta(months=2),
                             datetime.min.time(),
                         )),
                    ])
                    if not existing:
                        vals = {
                            'name': _('Inspection — %s') % (
                                line.equipment_id.name or self.name),
                            'equipment_id': line.equipment_id.id,
                            'service_contract_id': self.id,
                            'planned_start_datetime': datetime.combine(
                                insp_date, datetime.min.time()
                            ),
                            'product_tmpl_id': (
                                inspection_type.id
                                if inspection_type else False
                            ),
                            'billing_type': line.billing_type,
                            'elevata_contract_type':
                                line.contract_type_selection,
                        }
                        if (line.customer_id
                                and 'customer_id'
                                in self.env['fieldservice.order']._fields):
                            vals['customer_id'] = line.customer_id.id
                        insp_order = self.env['fieldservice.order'].create(vals)
                        self._generate_checklist_for_order(
                            insp_order, line.equipment_id
                        )
                        created_count += 1
                    insp_date += relativedelta(years=1)
        return created_count

    def _generate_checklist_for_order(self, order, location):
        if 'fieldservice.checklist' not in self.env.registry:
            return
        elevator_type = location.elevator_type_id
        if not elevator_type:
            return
        domain = [
            '|',
            ('elevator_type_ids', '=', False),
            ('elevator_type_ids', 'in', elevator_type.id),
        ]
        checklists = self.env['fieldservice.checklist'].search(domain)
        items = []
        for checklist in checklists:
            for line in checklist.line_ids:
                items.append((0, 0, {
                    'checklist_line_id': line.id,
                    'name': line.name,
                    'sequence': line.sequence,
                }))
        if items:
            order.write({'checklist_item_ids': items})

    # ── Renewal reminder ──

    def _schedule_renewal_reminder(self):
        self.ensure_one()
        if not self.date_end:
            return
        reminder_date = self.date_end - relativedelta(days=90)
        if reminder_date > fields.Date.today():
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=reminder_date,
                summary=_('Contract renewal — contact customer'),
                note=_('Contract %s expires %s (in 90 days). '
                       'Contact customer for renewal.') % (
                    self.name, self.date_end
                ),
            )

    # ── Cron jobs ──

    def _auto_create_invoice(self):
        self.ensure_one()
        lines = self.line_ids.filtered(lambda l: l.billing_type == 'prepaid')
        if not lines:
            return False
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'service_contract_id': self.id,
            'invoice_date': fields.Date.today(),
            'invoice_payment_term_id': (
                self.payment_term_id.id
                or self.partner_id.property_payment_term_id.id
                or False
            ),
            'invoice_line_ids': [
                (0, 0, {
                    'name': _('Service Contract %s — %s') % (
                        self.name,
                        line.equipment_id.name if line.equipment_id else '',
                    ),
                    'quantity': 1.0,
                    'price_unit': self._get_period_amount(line),
                })
                for line in lines
            ],
        })
        return invoice

    @api.model
    def _cron_auto_invoice(self):
        today = fields.Date.today()
        due = self.search([
            ('state', '=', 'confirmed'),
            ('billing_interval', '!=', 'manual'),
            ('next_invoice_date', '<=', today),
            ('date_end', '>=', today),
        ])
        for contract in due:
            try:
                contract._auto_create_invoice()
                contract.next_invoice_date = (
                    contract._get_next_invoice_date(today)
                )
            except Exception as e:
                contract.message_post(
                    body=_('Automatic invoicing failed: %s') % str(e)
                )

    @api.model
    def _cron_renewal_reminder(self):
        today = fields.Date.today()
        target_date = today + relativedelta(days=90)
        expiring = self.search([
            ('state', '=', 'confirmed'),
            ('date_end', '=', target_date),
        ])
        for contract in expiring:
            already = self.env['mail.activity'].search([
                ('res_model', '=', 'elevata.service.contract'),
                ('res_id', '=', contract.id),
                ('summary', 'ilike', 'renewal'),
            ], limit=1)
            if not already:
                contract.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=target_date,
                    summary=_('Contract renewal — contact customer'),
                    note=_('Contract %s expires %s (in 90 days). '
                           'Contact customer for renewal.') % (
                        contract.name, contract.date_end
                    ),
                )

    @api.model
    def _cron_check_expired(self):
        today = fields.Date.today()
        expired = self.search([
            ('state', '=', 'confirmed'),
            ('date_end', '<', today),
        ])
        if expired:
            expired.write({'state': 'expired'})

    @api.model
    def _cron_generate_service_orders(self):
        confirmed = self.search([
            ('state', '=', 'confirmed'),
            ('date_end', '>=', fields.Date.today()),
        ])
        for contract in confirmed:
            contract._generate_orders_for_contract()

    # ── CRUD ──

    def unlink(self):
        for rec in self:
            if rec.fsm_order_ids:
                raise UserError(
                    _('Cannot delete contract "%s" with %d linked '
                      'work order(s). Remove them first or cancel '
                      'the contract instead.')
                    % (rec.name, len(rec.fsm_order_ids))
                )
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code(
                        'elevata.service.contract'
                    ) or 'New'
                )
        return super().create(vals_list)
