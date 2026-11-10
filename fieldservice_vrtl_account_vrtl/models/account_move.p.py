from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class FieldServiceOrder(models.Model):
    _inherit = 'account.move'
    fieldservice_order_id = fields.Many2one(
            'fieldservice.order',
            string='Fieldservice')
