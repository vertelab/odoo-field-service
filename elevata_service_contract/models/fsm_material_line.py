from odoo import api, fields, models


class ElevataFsmMaterialLine(models.Model):
    _name = 'elevata.fsm.material.line'
    _description = 'Work Order Material Line'
    _order = 'id'

    fsm_order_id = fields.Many2one(
        'fieldservice.order',
        string='Work Order',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product/Material',
    )
    name = fields.Char(string='Description')
    quantity = fields.Float(string='Quantity', default=1.0, digits=(10, 2))
    price_unit = fields.Float(string='Unit Price (SEK)', digits=(16, 2))
    amount = fields.Float(
        string='Amount',
        compute='_compute_amount',
        store=True,
        digits=(16, 2),
    )

    @api.depends('quantity', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.lst_price
