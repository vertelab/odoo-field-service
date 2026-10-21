from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    service_contract_count = fields.Integer(
        string='Service Contracts',
        compute='_compute_service_contract_count',
    )

    def _compute_service_contract_count(self):
        for partner in self:
            partner.service_contract_count = (
                self.env['elevata.service.contract'].search_count([
                    ('partner_id', 'child_of', partner.id),
                    ('state', '=', 'confirmed'),
                ])
            )

    def action_view_service_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Service Contracts',
            'res_model': 'elevata.service.contract',
            'view_mode': 'tree,form',
            'domain': [('partner_id', 'child_of', self.id)],
            'context': {'default_partner_id': self.id},
        }
