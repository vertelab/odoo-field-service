from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    model = fields.Char(string='Model', help="The model name or number of the product")
    product_number = fields.Char(string='Product Number', help="The product number or part number")
    product_type = fields.Many2one('fieldservice.order.type', string='Product Type')

