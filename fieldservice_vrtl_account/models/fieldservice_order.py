from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'
    invoice_line_ids = fields.One2many(
            'fieldservice.invoice.line',
            'order_id',
            string='Invoice Lines'
        )
        
    account_move_ids = fields.One2many('account.move','fieldservice_order_id',string="invoices")
    invoice_count = fields.Integer(
    string="Invoice Count",
    compute="_compute_invoice_count"
)

    def _compute_invoice_count(self):
        for order in self:
            order.invoice_count = len(order.account_move_ids)

    def create_invoices(self):
        invoice_vals_list = self.get_invoice_vals()
        invoices = self.env['account.move']
        for invoice_vals in invoice_vals_list:
            invoices |= self.env['account.move'].create(invoice_vals)
        return invoices

        
    def get_invoice_data(self):
        for order in self:
            for invoice_line_id in invoice_line_ids:
                invoice_line_ids.delivered = 1
                invoice_line_ids.invoiced = 1
    
    
    def get_invoice_vals(self):
        vals_list = []
        for order in self:
            line_vals = []
            for line in order.invoice_line_ids:
                qty_to_invoice = line.delivered - line.invoiced
                if qty_to_invoice > 0:
                    line_vals.append({
                        'product_id': line.product_id.id,
                        'quantity': qty_to_invoice,
                        'price_unit': line.price,
                        'tax_ids': [(6, 0, [line.tax_id.id])] if line.tax_id else [],
                        'name': line.product_id.display_name,
                    })
            if line_vals:
                vals = {
                    'fieldservice_order_id': order.id,
                    'partner_id': order.partner_id.id,
                    'move_type': 'out_invoice',
                    'invoice_line_ids': [(0, 0, line) for line in line_vals],
                }
                vals_list.append(vals)
        return vals_list
        
    def action_view_invoices(self):
            self.ensure_one()
            action = self.env.ref('account.action_move_out_invoice_type').read()[0]
            action['domain'] = [('fieldservice_order_id', '=', self.id)]
            action['context'] = {
                'default_fieldservice_order_id': self.id,
                'default_partner_id': self.partner_id.id,
            }
            return action


    

class FieldServiceInvoiceLine(models.Model):
    _name = 'fieldservice.invoice.line'
    _description = 'Field Service Invoice Line'

    order_id = fields.Many2one('fieldservice.order', string='Service Order', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    delivered = fields.Float(string='Delivered Quantity', default=0.0)
    invoiced = fields.Float(string='Invoiced Quantity', default=0.0)
    price = fields.Float(string='Unit Price', required=True)
    tax_id = fields.Many2one('account.tax', string='Tax')
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            # Set price from product
            self.price = self.product_id.lst_price
            # Set tax from product (assuming product has a tax_id or taxes_id field)
            taxes = self.product_id.taxes_id
            self.tax_id = taxes and taxes[0].id or False
        else:
            self.price = 0.0
            self.tax_id = False
