from odoo import api, fields, models, _

class FieldServiceStakeHolder(models.Model):
    _name = 'fieldservice.stakeholder'
    _description = 'Field Service Stakholder'

    partner_id = fields.Many2one('res.partner', string="Partner")
    partner_status = fields.Selection([('legal_owner', 'Legal Owner'),
                                       ], string="Status", default='legal_owner')

    order_id = fields.Many2one('fieldservice.order', string='Service Order', required=True)

    name = fields.Char(string="Name", related="partner_id.name", store=True)
