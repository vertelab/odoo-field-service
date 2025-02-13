from odoo import models, fields

class FieldServiceOrderLineExtend(models.Model):
    _inherit = 'fieldservice.order.line'

    used_material_ids = fields.One2many('fieldservice.order.line.material', 'order_line_id', string='Used Materials')
    requested_material_ids = fields.One2many('fieldservice.order.line.material.request', 'order_line_id', string='Requested Materials')
