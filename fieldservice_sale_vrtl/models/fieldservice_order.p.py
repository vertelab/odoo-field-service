from odoo import fields, models, api, _

class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'

    sale_order_line_id = fields.Many2one('sale.order.line', string='Sales Order Line')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', related='sale_order_line_id.order_id', store=True)
    my_sale_orders_filter = fields.Boolean(compute='_compute_my_sale_orders_filter')


    @api.depends('sale_order_line_id')
    def _compute_sale_order(self):
        for order in self:
            order.sale_order_id = order.sale_order_line_id.order_id if order.sale_order_line_id else False


    @api.depends('sale_order_id')
    def _compute_my_sale_orders_filter(self):
        for record in self:
            record.my_sale_orders_filter = bool(record.sale_order_id)

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'context': {'default_sale_order_id': self.id}
        }

    
