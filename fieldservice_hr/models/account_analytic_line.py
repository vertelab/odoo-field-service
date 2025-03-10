from odoo import api, fields, models

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    fieldservice_order_line_id = fields.Many2one('fieldservice.order.line')
