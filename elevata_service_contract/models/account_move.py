from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    service_contract_id = fields.Many2one(
        'elevata.service.contract',
        string='Service Contract',
        ondelete='set null',
        index=True,
    )
