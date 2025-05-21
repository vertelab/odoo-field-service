from odoo import models, fields

class FieldServiceOrderLineMaterialRequest(models.Model):
    _name = 'fieldservice.order.line.material.request'
    _description = 'Field Service Order Line Material Request'
    _rec_name = 'product_id'

    order_line_id = fields.Many2one('fieldservice.order.line', string='Order Line')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(string='Quantity')
