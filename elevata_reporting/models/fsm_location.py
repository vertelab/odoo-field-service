from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class FSMLocationReporting(models.Model):
    _inherit = 'maintenance.equipment'

    repeat_order_count = fields.Integer(
        string='Orders Last 6 Months',
        compute='_compute_repeat_order_count',
        help='Number of work orders in the last 6 months. >=3 indicates recurring problems.',
    )
    repeat_problem_warning = fields.Boolean(
        string='Recurring Problem',
        compute='_compute_repeat_order_count',
        store=False,
        help='True if >=3 work orders created on this elevator in the last 6 months.',
    )
    has_active_contract = fields.Boolean(
        string='Has Active Contract',
        compute='_compute_has_active_contract',
        store=False,
    )
    inspection_soon = fields.Boolean(
        string='Inspection Within 60 Days',
        compute='_compute_inspection_soon',
        store=False,
    )
    warranty_order_count = fields.Integer(
        string='Warranty Orders',
        compute='_compute_warranty_order_count',
        store=False,
        help='Total number of warranty work orders on this elevator.',
    )

    @api.depends()
    def _compute_repeat_order_count(self):
        cutoff = date.today() - relativedelta(months=6)
        Order = self.env['fieldservice.order']
        for location in self:
            count = Order.search_count([
                ('equipment_id', '=', location.id),
                ('create_date', '>=', datetime.combine(cutoff, datetime.min.time())),
            ])
            location.repeat_order_count = count
            location.repeat_problem_warning = count >= 3

    @api.depends()
    def _compute_has_active_contract(self):
        if 'elevata.service.contract.line' not in self.env.registry:
            for loc in self:
                loc.has_active_contract = False
            return
        ContractLine = self.env['elevata.service.contract.line']
        for location in self:
            location.has_active_contract = ContractLine.search_count([
                ('equipment_id', '=', location.id),
                ('service_contract_id.state', '=', 'confirmed'),
            ]) > 0

    @api.depends()
    def _compute_warranty_order_count(self):
        Order = self.env['fieldservice.order']
        for location in self:
            location.warranty_order_count = Order.search_count([
                ('equipment_id', '=', location.id),
                ('is_warranty', '=', True),
            ])

    def action_view_fsm_orders_reporting(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Work Orders',
            'res_model': 'fieldservice.order',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {},
        }

    @api.depends()
    def _compute_inspection_soon(self):
        today = date.today()
        threshold = today + relativedelta(days=60)
        for location in self:
            nd = location.next_inspection_date
            if nd and today <= nd <= threshold:
                location.inspection_soon = True
            else:
                location.inspection_soon = False
