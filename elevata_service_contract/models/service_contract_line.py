from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ServiceContractLine(models.Model):
    _name = 'elevata.service.contract.line'
    _description = 'Service Contract Line'
    _order = 'id'

    service_contract_id = fields.Many2one(
        'elevata.service.contract',
        string='Contract',
        required=True,
        ondelete='cascade',
    )
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Elevator',
        required=True,
        domain=[('elevator_type_id', '!=', False)],
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Billing Customer',
        compute='_compute_customer_id',
        store=True,
    )
    visits_per_year = fields.Selection([
        ('1', '1 visit/year'),
        ('2', '2 visits/year'),
        ('4', '4 visits/year'),
        ('6', '6 visits/year'),
        ('12', '12 visits/year'),
    ], string='Visits per Year', required=True)

    include_inspection = fields.Boolean(
        string='Include Inspection',
        default=True,
        help='Include yearly safety inspection in the contract '
             '(uses inspection month from elevator)',
    )
    price_unit = fields.Float(
        string='Unit Price',
        required=True,
        digits='Product Price',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='service_contract_id.company_id',
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
        store=True,
    )
    contract_type_selection = fields.Selection([
        ('SERV-VB', 'On Demand'),
        ('SERV-STD', 'Standard'),
        ('SERV-FULL', 'Full Service'),
        ('SERV-GAR', 'Warranty'),
    ], string='Contract Type', required=True)

    billing_type = fields.Selection([
        ('prepaid', 'Prepaid'),
        ('postpaid', 'Invoiced Per Visit'),
    ], string='Billing', default='postpaid', required=True)

    contract_description = fields.Text(
        string='Contract Description',
        compute='_compute_contract_description',
        store=True,
    )

    @api.depends('equipment_id')
    def _compute_customer_id(self):
        for line in self:
            eq = line.equipment_id
            # maintenance.equipment has no customer_id; the customer is the
            # owner. Fall back to the contract partner when the equipment has
            # no owner set.
            if eq and 'customer_id' in eq._fields and eq.customer_id:
                line.customer_id = eq.customer_id
            elif eq and eq.partner_id:
                line.customer_id = eq.partner_id
            elif line.service_contract_id.partner_id:
                line.customer_id = line.service_contract_id.partner_id
            else:
                line.customer_id = False

    @api.onchange('contract_type_selection')
    def _onchange_contract_type_billing(self):
        for line in self:
            if line.contract_type_selection == 'SERV-VB':
                line.billing_type = 'postpaid'
            elif line.contract_type_selection:
                line.billing_type = 'prepaid'

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        if self.equipment_id:
            self.customer_id = (
                self.equipment_id.customer_id
                or self.equipment_id.owner_id
                or False
            )

    @api.constrains('visits_per_year')
    def _check_visits_per_year(self):
        for line in self:
            if not line.visits_per_year:
                raise ValidationError(
                    _('Number of visits per year must be specified')
                )

    @api.depends('contract_type_selection')
    def _compute_contract_description(self):
        for line in self:
            if line.contract_type_selection == 'SERV-VB':
                line.contract_description = (
                    'On-demand service contract without fixed cost. '
                    'Invoiced per visit. On-call and spare parts '
                    'charged according to pricelist.'
                )
            elif line.contract_type_selection == 'SERV-STD':
                line.contract_description = (
                    'Standard contract with fixed annual fee. 1-12 planned '
                    'visits per year. On-call and spare parts charged '
                    'according to pricelist. Automatic service scheduling.'
                )
            elif line.contract_type_selection == 'SERV-FULL':
                line.contract_description = (
                    'Full service contract with fixed annual fee. 1-12 planned '
                    'visits per year. On-call and selected spare parts included. '
                    'Automatic service scheduling and prioritized service.'
                )
            elif line.contract_type_selection == 'SERV-GAR':
                line.contract_description = (
                    'Warranty contract without service cost. Planned visits '
                    'according to warranty terms. On-call and spare parts included '
                    'per warranty terms. Automatic service scheduling.'
                )
            else:
                line.contract_description = False
