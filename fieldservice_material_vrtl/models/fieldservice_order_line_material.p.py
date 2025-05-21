from odoo import models, fields

class FieldServiceOrderLineMaterial(models.Model):
    _name = 'fieldservice.order.line.material'
    _description = 'Field Service Order Line Material'
    _rec_name = 'product_id'

    order_line_id = fields.Many2one('fieldservice.order.line', string='Order Line')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(string='Quantity')
    