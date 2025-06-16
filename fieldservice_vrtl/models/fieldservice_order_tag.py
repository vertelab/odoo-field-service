from odoo import models, fields, api


class FieldServiceOrderTags(models.Model):
    _name = "field.service.order.tag"
    _description = "Field Service Order Tag"

    name = fields.Char(string="Tag")
    color = fields.Integer(string="Color")