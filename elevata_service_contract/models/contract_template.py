from odoo import api, fields, models


class ContractTemplate(models.Model):
    _name = 'elevata.contract.template'
    _description = 'Contract Template'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=10)
    content = fields.Html('Content', sanitize=False)
    description = fields.Text('Description')
    position = fields.Selection([
        ('before', 'Before'),
        ('after', 'After'),
    ], string='Position', default='after', required=True)
    contract_type = fields.Selection([
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Contract Type', default='standard', required=True)
    category = fields.Selection([
        ('header', 'Header'),
        ('terms', 'Terms & Conditions'),
        ('footer', 'Footer'),
        ('custom', 'Custom Section'),
    ], string='Category', default='custom', required=True)
    is_active = fields.Boolean('Active', default=True)
    is_locked = fields.Boolean(
        'Locked',
        default=False,
        help='If locked, this template cannot be modified by users',
    )
    last_modified = fields.Datetime('Last Modified', readonly=True)
    modified_by = fields.Many2one(
        'res.users',
        string='Modified By',
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['last_modified'] = fields.Datetime.now()
            vals['modified_by'] = self.env.user.id
        return super().create(vals_list)

    def write(self, vals):
        vals.update({
            'last_modified': fields.Datetime.now(),
            'modified_by': self.env.user.id,
        })
        return super().write(vals)
