from odoo import _, api, fields, models

CONTRACT_TYPE = [
    ('SERV-VB', 'On Demand'),
    ('SERV-STD', 'Standard'),
    ('SERV-FULL', 'Full Service'),
    ('SERV-GAR', 'Warranty'),
]


class FSMLocation(models.Model):
    _inherit = 'maintenance.equipment'

    active_service_contract_id = fields.Many2one(
        'elevata.service.contract',
        string='Aktivt serviceavtal',
        compute='_compute_active_service_contract',
    )
    active_contract_type = fields.Selection(
        CONTRACT_TYPE,
        string='Avtalstyp',
        compute='_compute_active_service_contract',
    )

    require_service_checklist = fields.Boolean(
        string='Kräv servicechecklista',
        default=False,
        help='Om aktiverad: checklista genereras automatiskt på serviceordrar '
             'och måste fyllas i innan order kan slutföras.',
    )
    custom_checklist_line_ids = fields.One2many(
        'elevata.location.checklist.line',
        'equipment_id',
        string='Anpassad checklista',
    )

    service_contract_count = fields.Integer(
        string='Active Contracts',
        compute='_compute_service_contract_count',
    )
    invoice_count = fields.Integer(
        string='Invoices',
        compute='_compute_invoice_count',
    )
    annual_visits = fields.Char(
        string='Service Visits/Year',
        compute='_compute_annual_visits',
    )

    def _compute_active_service_contract(self):
        ContractLine = self.env['elevata.service.contract.line']
        for location in self:
            line = ContractLine.search([
                ('equipment_id', '=', location.id),
                ('service_contract_id.state', '=', 'confirmed'),
            ], limit=1, order='id desc')
            location.active_service_contract_id = (
                line.service_contract_id.id if line else False
            )
            location.active_contract_type = (
                line.contract_type_selection if line else False
            )

    def _compute_annual_visits(self):
        ContractLine = self.env['elevata.service.contract.line']
        visit_labels = dict(
            ContractLine._fields['visits_per_year']._description_selection(
                self.env
            )
        )
        for location in self:
            line = ContractLine.search([
                ('equipment_id', '=', location.id),
                ('service_contract_id.state', '=', 'confirmed'),
            ], limit=1, order='id desc')
            if line and line.visits_per_year:
                location.annual_visits = visit_labels.get(
                    line.visits_per_year, line.visits_per_year
                )
            else:
                location.annual_visits = False

    def _compute_service_contract_count(self):
        ContractLine = self.env['elevata.service.contract.line']
        for location in self:
            contract_ids = ContractLine.search([
                ('equipment_id', '=', location.id),
                ('service_contract_id.state', '=', 'confirmed'),
            ]).mapped('service_contract_id').ids
            location.service_contract_count = len(set(contract_ids))

    def _location_invoices(self):
        """Invoices linked to this location via FSM orders."""
        moves = self.env['account.move'].search([
            '|',
            ('fsm_equipment_id', 'in', self.ids),
            ('fsm_order_ids.equipment_id', 'in', self.ids),
            ('move_type', '=', 'out_invoice'),
        ])
        orders = self.env['fieldservice.order'].search([
            ('equipment_id', 'in', self.ids),
        ])
        return moves | orders.mapped('invoice_lines.move_id').filtered(
            lambda m: m.move_type == 'out_invoice'
        )

    def _compute_invoice_count(self):
        for location in self:
            location.invoice_count = len(location._location_invoices())

    def action_view_invoices(self):
        self.ensure_one()
        invoice_ids = self._location_invoices().ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoice_ids)],
            'context': {'default_move_type': 'out_invoice'},
        }

    def action_open_active_contract(self):
        self.ensure_one()
        if self.active_service_contract_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'elevata.service.contract',
                'res_id': self.active_service_contract_id.id,
                'view_mode': 'form',
            }

    def action_populate_checklist(self):
        self.ensure_one()
        if 'elevata.service.checklist' not in self.env.registry:
            return
        elevator_type = self.elevator_type_id
        if not elevator_type:
            return
        domain = [
            '|',
            ('elevator_type_ids', '=', False),
            ('elevator_type_ids', 'in', elevator_type.id),
        ]
        checklists = self.env['elevata.service.checklist'].search(domain)
        lines = []
        for checklist in checklists:
            for line in checklist.line_ids:
                lines.append((0, 0, {
                    'name': line.name,
                    'sequence': line.sequence,
                }))
        if lines:
            self.custom_checklist_line_ids.unlink()
            self.write({'custom_checklist_line_ids': lines})

    def action_view_service_contracts(self):
        self.ensure_one()
        contract_ids = self.env['elevata.service.contract.line'].search([
            ('equipment_id', '=', self.id),
        ]).mapped('service_contract_id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Service Contracts'),
            'res_model': 'elevata.service.contract',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', list(set(contract_ids)))],
            'context': {},
        }
