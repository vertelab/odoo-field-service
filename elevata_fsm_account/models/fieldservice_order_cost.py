from odoo import api, fields, models


class FieldServiceOrderCost(models.Model):
    _name = 'fieldservice.order.cost'
    _description = 'Field Service Order Cost'

    order_id = fields.Many2one(
        'fieldservice.order', string="Order", required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        'res.partner', string="Vendor",
        help='Contractor to bill. Required to create a vendor bill.',
    )
    product_id = fields.Many2one(
        'product.product', string="Product", required=True,
    )
    quantity = fields.Float(string="Quantity", required=True, default=1.0)
    price_unit = fields.Float(string="Unit Price", required=True)
    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self.env.company,
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.standard_price
