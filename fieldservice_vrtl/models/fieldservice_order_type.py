from odoo import models, fields

class FieldsOrderType(models.Model):
    _name = 'fieldservice.order.type'
    _description = 'Field Service Order Type'

    name = fields.Char(string = 'Name', required = True)
