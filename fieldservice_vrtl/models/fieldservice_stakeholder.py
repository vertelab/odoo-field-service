from odoo import api, fields, models, _

class FieldServiceStakeHolder(models.Model):
    _name = 'fieldservice.stakeholder'
    _description = 'Field Service Stakholder'

    partner_id = fields.Many2one('res.partner', ondelete='cascade', string="Partner")
    partner_status = fields.Selection([('legal_owner', 'Legal Owner'),
                                       ],ondelete='cascade', string="Status", default='legal_owner')

    order_id = fields.Many2one('fieldservice.order', string='Service Order', ondelete='cascade', required=True)

    name = fields.Char(string="Name", related="partner_id.name", ondelete='cascade', store=True)
