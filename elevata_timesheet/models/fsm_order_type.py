from odoo import fields, models


class FSMOrderType(models.Model):
    _inherit = 'fieldservice.order.type'

    verksamhetstyp_analytic_id = fields.Many2one(
        'account.analytic.account',
        string="Activity Type (Analytic Account)",
        domain="[('plan_id', '=', 4)]",
    )
