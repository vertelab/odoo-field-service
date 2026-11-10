from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        compute='_compute_analytic_account_id',
        store=True,
        readonly=False,
        help='Inherited from the property when the elevator has one. '
             'Overrides it when a lift needs its own cost tracking.',
    )

    @api.depends('property_id.analytic_account_id')
    def _compute_analytic_account_id(self):
        for equipment in self:
            equipment.analytic_account_id = (
                equipment.property_id.analytic_account_id
            )


class PropertyProperty(models.Model):
    _inherit = 'property.property'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        help='Cost tracking for this property. Elevators on the property '
             'inherit it unless they set their own.',
    )
