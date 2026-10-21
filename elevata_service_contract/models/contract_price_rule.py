from odoo import api, fields, models

CONTRACT_TYPE = [
    ('SERV-VB', 'On Demand'),
    ('SERV-STD', 'Standard'),
    ('SERV-FULL', 'Full Service'),
    ('SERV-GAR', 'Warranty'),
]

RATE_TYPE = [
    ('normaltid', 'Normal Time (Mon-Fri 07:00-16:00)'),
    ('overtid_1_2h', 'Overtime 1-2 h'),
    ('overtid_2h_plus', 'Overtime after 2 h'),
    ('lordag', 'Saturday'),
    ('sondag_helgdag', 'Sunday/Holiday'),
    ('storhelg', 'Major Holiday'),
    ('beredskap_vardag', 'Standby Weekday'),
    ('beredskap_helg', 'Standby Weekend'),
    ('jourutryckning', 'Emergency Call-out (min 3 h)'),
    ('restid', 'Travel Time'),
    ('servicebil_mil', 'Service Vehicle (SEK/10km)'),
    ('servicebil_tid', 'Service Vehicle Time'),
    ('servicebil_fast', 'Service Vehicle Fixed Fee (SEK)'),
    ('verktygsavgift', 'Tool Fee'),
    ('overtid', 'Overtime (legacy)'),
    ('jour', 'On-call (legacy)'),
]


class ElevataContractPriceRule(models.Model):
    _name = 'elevata.contract.price.rule'
    _description = 'Contract-specific Price Rule'
    _order = 'rule_type, sequence'

    service_contract_id = fields.Many2one(
        'elevata.service.contract',
        string='Service Contract',
        required=False,
        ondelete='cascade',
    )
    offer_id = fields.Many2one(
        'elevata.offer',
        string='Offer',
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Sequence', default=10)

    rule_type = fields.Selection([
        ('annual_fee', 'Annual Service Fee'),
        ('hourly', 'Hourly Rate'),
        ('material_markup', 'Material Markup %'),
        ('product_price', 'Fixed Product Price / Subscription'),
        ('included', 'Included in Contract (not invoiced)'),
    ], string='Rule Type', required=True)

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Elevator',
        help='Empty = applies to all elevators on the contract',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='Empty = applies to all products of this rule type',
    )
    contract_type = fields.Selection(
        CONTRACT_TYPE,
        string='Contract Type',
        help='Empty = applies to all contract types',
    )
    rate_type = fields.Selection(
        RATE_TYPE,
        string='Time Type',
        help='Used for hourly rate and "included" rules',
    )
    price = fields.Float(
        string='Price (SEK)',
        digits=(16, 2),
        help='Fixed price in SEK — used if discount % = 0',
    )
    discount_pct = fields.Float(
        string='Discount %',
        digits=(5, 2),
        help='Discount in % against base price from pricelist',
    )
    is_included = fields.Boolean(
        string='Included in Contract',
        default=False,
        help='Service/product is included — not invoiced',
    )
    note = fields.Char(string='Comment')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        compute='_compute_company_id',
        store=True,
        readonly=True,
    )

    @api.depends('service_contract_id.company_id', 'offer_id')
    def _compute_company_id(self):
        for rec in self:
            rec.company_id = (
                rec.service_contract_id.company_id
                or rec.offer_id.company_id
            )

    @api.onchange('rule_type')
    def _onchange_rule_type(self):
        if self.rule_type == 'included':
            self.is_included = True
            self.price = 0.0
            self.discount_pct = 0.0
        elif self.rule_type == 'material_markup':
            self.product_id = False
            self.rate_type = False
        elif self.rule_type == 'annual_fee':
            self.rate_type = False

    def _compute_display_name(self):
        type_labels = dict(
            self._fields['rule_type']._description_selection(self.env)
        )
        rate_labels = dict(
            self._fields['rate_type']._description_selection(self.env)
        )
        for rec in self:
            label = type_labels.get(rec.rule_type, rec.rule_type)
            parts = [label]
            if rec.equipment_id:
                parts.append(rec.equipment_id.name)
            if rec.product_id:
                parts.append(rec.product_id.name)
            if rec.rate_type:
                parts.append(rate_labels.get(rec.rate_type, rec.rate_type))
            rec.display_name = ' — '.join(parts)
