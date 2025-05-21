from odoo import fields, models, api, _
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    service_tracking = fields.Selection(
        selection_add=[
            ('fieldservice_only', 'Fieldservice'),
        ], ondelete={
            'fieldservice_only': 'set default',
        },
    )
