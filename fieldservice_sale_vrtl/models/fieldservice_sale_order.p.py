from odoo import models, fields, api, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    fieldservice_order_id = fields.Many2one('fieldservice.order')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        
        for line in self.order_line:
            product = line.product_id
            if product.type == 'service' and product.service_tracking == 'fieldservice_only':
                fieldservice_order = self.env['fieldservice.order'].create({
                    'name': f"{self.name} - {line.name}",
                    'sale_order_id': self.id,
                    'sale_order_line_id': line.id,
                })
                line.fieldservice_order_id = fieldservice_order.id
        
        return res


    fieldservice_count = fields.Integer(string='Fieldservice Orders', compute='_compute_fieldservice_count')    

    def _compute_fieldservice_count(self):
        for order in self:
            order.fieldservice_count = len(order.order_line.mapped('fieldservice_order_id'))


    def action_view_fieldservice_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fieldservice Orders',
            'view_mode': 'list,form',
            'res_model': 'fieldservice.order',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id}
        }
        
    
    



        # fieldservice_order_ids = fields.One2many('fieldservice.order', 'sale_order_id', string='Field Service Orders')
    
    # @api.depends('fieldservice_order_ids')
    # def _compute_fieldservice_order_count(self):
    #     for order in self:
    #         order.fieldservice_order_count = len(order.fieldservice_order_ids)

    # def action_view_fieldservice_orders(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Field Service Sale Orders',
    #         'view_mode': 'form',
    #         'res_model': 'fieldservice.order',
    #         'domain': [('sale_order_id', '=', self.id)],
    #         'context': {'default_sale_order_id': self.id}
    #     }