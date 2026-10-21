from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

CONTRACT_TYPE = [
    ('SERV-VB', 'On Demand'),
    ('SERV-STD', 'Standard'),
    ('SERV-FULL', 'Full Service'),
    ('SERV-GAR', 'Warranty'),
]


class FSMOrder(models.Model):
    _inherit = 'fieldservice.order'

    service_contract_id = fields.Many2one(
        'elevata.service.contract',
        string='Service Contract',
        ondelete='restrict',
    )
    location_active_contract_id = fields.Many2one(
        related='equipment_id.active_service_contract_id',
        string='Aktivt serviceavtal (live)',
        readonly=True,
    )
    billing_type = fields.Selection([
        ('prepaid', 'Prepaid'),
        ('postpaid', 'Post-paid'),
    ], string='Billing', default='postpaid')

    billing_interval = fields.Selection(
        related='service_contract_id.billing_interval',
        string='Billing Interval',
        readonly=True,
        store=False,
    )
    is_warranty = fields.Boolean(
        string='Warranty Job',
        compute='_compute_is_warranty',
        store=True,
        tracking=True,
        help='Automatically set when contract type is Warranty (SERV-GAR).',
    )
    contract_visits_per_year = fields.Char(
        string='Antal besök/år',
        compute='_compute_contract_visits',
    )
    live_contract_type = fields.Selection(
        CONTRACT_TYPE,
        string='Avtalstyp (live)',
        compute='_compute_live_contract_info',
    )
    live_visits_per_year = fields.Char(
        string='Antal besök/år (live)',
        compute='_compute_live_contract_info',
    )
    billing_label = fields.Char(
        string='Billing Status',
        compute='_compute_billing_label',
    )
    elevata_contract_type = fields.Selection(
        CONTRACT_TYPE,
        string='Contract Type',
        readonly=True,
        help='Contract type from service contract — controls hourly rates',
    )

    time_line_ids = fields.One2many(
        'elevata.fsm.time.line',
        'fsm_order_id',
        string='Time Report',
    )
    time_total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_time_totals',
        store=True,
        digits=(10, 2),
    )
    time_total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_time_totals',
        store=True,
        digits=(16, 2),
    )

    rate_normaltid = fields.Float(
        string='Normal Time (SEK/h)',
        compute='_compute_contracted_rates',
        digits=(16, 2),
    )
    rate_overtid = fields.Float(
        string='Overtime (SEK/h)',
        compute='_compute_contracted_rates',
        digits=(16, 2),
    )
    rate_jour = fields.Float(
        string='On-call (SEK/h)',
        compute='_compute_contracted_rates',
        digits=(16, 2),
    )

    material_line_ids = fields.One2many(
        'elevata.fsm.material.line',
        'fsm_order_id',
        string='Material',
    )
    material_total_amount = fields.Float(
        string='Total Material (SEK)',
        compute='_compute_material_totals',
        store=True,
        digits=(16, 2),
    )

    location_require_checklist = fields.Boolean(
        related='equipment_id.require_service_checklist',
        string='Hiss kräver checklista',
    )
    type_use_service_checklist = fields.Boolean(
        related='product_tmpl_id.product_type.use_service_checklist',
        string='Ordertyp använder checklista',
    )

    checklist_item_ids = fields.One2many(
        'elevata.service.checklist.item',
        'fsm_order_id',
        string='Checklist',
    )
    checklist_count = fields.Integer(
        string='Checklist Items',
        compute='_compute_checklist_count',
    )
    checklist_done_count = fields.Integer(
        string='Done',
        compute='_compute_checklist_count',
    )

    @api.onchange('equipment_id', 'type')
    def _onchange_location_set_description(self):
        if not self.equipment_id:
            return
        if (self.equipment_id.require_service_checklist
                and self.type.use_service_checklist):
            if not self.checklist_item_ids:
                self._onchange_populate_checklist()
        else:
            if not self.description:
                self.description = 'Service'

    def _onchange_populate_checklist(self):
        location = self.equipment_id
        items = []
        if location.custom_checklist_line_ids:
            for line in location.custom_checklist_line_ids:
                items.append((0, 0, {
                    'name': line.name,
                    'sequence': line.sequence,
                }))
        else:
            if 'elevata.service.checklist' not in self.env.registry:
                return
            elevator_type = location.elevator_type_id
            if not elevator_type:
                return
            domain = [
                '|',
                ('elevator_type_ids', '=', False),
                ('elevator_type_ids', 'in', elevator_type.id),
            ]
            checklists = self.env['elevata.service.checklist'].search(domain)
            for checklist in checklists:
                for line in checklist.line_ids:
                    items.append((0, 0, {
                        'checklist_line_id': line.id,
                        'name': line.name,
                        'sequence': line.sequence,
                    }))
        if items:
            self.checklist_item_ids = items

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('description'):
                loc_id = vals.get('equipment_id')
                if loc_id:
                    loc = self.env['maintenance.equipment'].browse(loc_id)
                    if not loc.require_service_checklist:
                        vals['description'] = 'Service'
        orders = super().create(vals_list)
        for order in orders:
            if (order.equipment_id
                    and order.equipment_id.require_service_checklist
                    and order.type.use_service_checklist
                    and not order.checklist_item_ids):
                self._auto_generate_checklist(order)
        return orders

    def _auto_generate_checklist(self, order):
        location = order.equipment_id
        items = []
        if location.custom_checklist_line_ids:
            for line in location.custom_checklist_line_ids:
                items.append((0, 0, {
                    'name': line.name,
                    'sequence': line.sequence,
                }))
        else:
            if 'elevata.service.checklist' not in self.env.registry:
                return
            elevator_type = location.elevator_type_id
            if not elevator_type:
                return
            domain = [
                '|',
                ('elevator_type_ids', '=', False),
                ('elevator_type_ids', 'in', elevator_type.id),
            ]
            checklists = self.env['elevata.service.checklist'].search(domain)
            for checklist in checklists:
                for line in checklist.line_ids:
                    items.append((0, 0, {
                        'checklist_line_id': line.id,
                        'name': line.name,
                        'sequence': line.sequence,
                    }))
        if items:
            order.write({'checklist_item_ids': items})

    @api.depends('material_line_ids.amount')
    def _compute_material_totals(self):
        for order in self:
            order.material_total_amount = sum(
                order.material_line_ids.mapped('amount')
            )

    @api.depends('time_line_ids.hours', 'time_line_ids.amount')
    def _compute_time_totals(self):
        for order in self:
            order.time_total_hours = sum(
                order.time_line_ids.mapped('hours')
            )
            order.time_total_amount = sum(
                order.time_line_ids.mapped('amount')
            )

    @api.depends('service_contract_id', 'elevata_contract_type')
    def _compute_contracted_rates(self):
        for order in self:
            pricelist = False
            if (order.service_contract_id
                    and order.service_contract_id.partner_id):
                pricelist = (
                    order.service_contract_id.partner_id.elevata_pricelist_id
                )
            if not pricelist and 'elevata.pricelist' in self.env.registry:
                pricelist = self.env['elevata.pricelist'].search(
                    [('active', '=', True)], limit=1, order='id asc'
                )
            if pricelist:
                order.rate_normaltid = pricelist.get_rate('normaltid')
                order.rate_overtid = pricelist.get_rate('overtid_1_2h')
                order.rate_jour = pricelist.get_rate('jourutryckning')
            else:
                order.rate_normaltid = 0.0
                order.rate_overtid = 0.0
                order.rate_jour = 0.0

    @api.depends('elevata_contract_type')
    def _compute_is_warranty(self):
        for order in self:
            order.is_warranty = order.elevata_contract_type == 'SERV-GAR'

    @api.depends('equipment_id', 'location_active_contract_id')
    def _compute_live_contract_info(self):
        ContractLine = self.env['elevata.service.contract.line']
        visit_labels = dict(
            ContractLine._fields['visits_per_year']._description_selection(
                self.env
            )
        )
        for order in self:
            contract = order.location_active_contract_id
            if contract and order.equipment_id:
                line = ContractLine.search([
                    ('service_contract_id', '=', contract.id),
                    ('equipment_id', '=', order.equipment_id.id),
                ], limit=1)
                if line:
                    order.live_contract_type = line.contract_type_selection
                    order.live_visits_per_year = visit_labels.get(
                        line.visits_per_year, line.visits_per_year
                    ) if line.visits_per_year else False
                else:
                    order.live_contract_type = False
                    order.live_visits_per_year = False
            else:
                order.live_contract_type = False
                order.live_visits_per_year = False

    @api.depends('service_contract_id', 'equipment_id')
    def _compute_contract_visits(self):
        ContractLine = self.env['elevata.service.contract.line']
        visit_labels = dict(
            ContractLine._fields['visits_per_year']._description_selection(
                self.env
            )
        )
        for order in self:
            if order.service_contract_id and order.equipment_id:
                line = ContractLine.search([
                    ('service_contract_id', '=', order.service_contract_id.id),
                    ('equipment_id', '=', order.equipment_id.id),
                ], limit=1)
                if line and line.visits_per_year:
                    order.contract_visits_per_year = visit_labels.get(
                        line.visits_per_year, line.visits_per_year
                    )
                else:
                    order.contract_visits_per_year = False
            else:
                order.contract_visits_per_year = False

    @api.depends('billing_type', 'service_contract_id', 'is_warranty')
    def _compute_billing_label(self):
        for order in self:
            if order.is_warranty:
                order.billing_label = _('Warranty job — not invoiced')
            elif (order.billing_type == 'prepaid'
                    and order.service_contract_id):
                order.billing_label = _('Included in contract (prepaid)')
            elif order.billing_type == 'postpaid' and order.service_contract_id:
                order.billing_label = _('Invoiced after completed work')
            else:
                order.billing_label = ''

    @api.depends('checklist_item_ids', 'checklist_item_ids.done')
    def _compute_checklist_count(self):
        for order in self:
            items = order.checklist_item_ids
            order.checklist_count = len(items)
            order.checklist_done_count = len(items.filtered('done'))

    def action_create_time_invoice(self):
        self.ensure_one()
        if self.is_warranty:
            raise UserError(
                _('Warranty jobs are not invoiced. Uncheck "Warranty Job" '
                  'if this should be invoiced.')
            )
        if not self.time_line_ids:
            raise UserError(_('No time lines to invoice.'))
        if not self.service_contract_id:
            raise UserError(
                _('Work order has no linked service contract.')
            )
        rate_labels = dict(
            self.env['elevata.fsm.time.line']._fields['rate_type']
            ._description_selection(self.env)
        )
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.service_contract_id.partner_id.id,
            'service_contract_id': self.service_contract_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (0, 0, {
                    'name': '%s — %s — %s' % (
                        self.name,
                        rate_labels.get(line.rate_type, line.rate_type),
                        line.date,
                    ),
                    'quantity': line.hours,
                    'price_unit': line.price_per_hour,
                })
                for line in self.time_line_ids
            ],
        })
        action = self.env['ir.actions.actions']._for_xml_id(
            'account.action_move_out_invoice_type'
        )
        action.update({
            'res_id': invoice.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
        })
        return action

    def action_complete(self):
        for order in self:
            if not order.resolution:
                raise ValidationError(
                    _('Fill in "Resolution" before completing the order.')
                )
            has_elevata = bool(
                order.time_line_ids or order.material_line_ids
            )
            has_std = (
                (hasattr(order, 'employee_timesheet_ids')
                 and bool(order.employee_timesheet_ids))
                or (hasattr(order, 'contractor_cost_ids')
                    and bool(order.contractor_cost_ids))
            )
            if not has_elevata and not has_std:
                raise UserError(
                    _('Add at least one time line or material line '
                      'before completing the order.')
                )
            if (order.equipment_id
                    and order.equipment_id.require_service_checklist
                    and order.type.use_service_checklist
                    and order.checklist_item_ids):
                undone = order.checklist_item_ids.filtered(
                    lambda i: not i.done
                )
                if undone:
                    raise ValidationError(
                        _('All checklist items must be completed before '
                          'closing this order. %d item(s) remaining.')
                        % len(undone)
                    )
        # Skip fieldservice_elevata_flow duplicate check via MRO
        mro = type(self).__mro__
        skip = False
        for cls in mro:
            if 'fieldservice_elevata_flow' in (cls.__module__ or ''):
                skip = True
                continue
            if skip and 'action_complete' in cls.__dict__:
                return cls.action_complete(self)
        return super().action_complete()
