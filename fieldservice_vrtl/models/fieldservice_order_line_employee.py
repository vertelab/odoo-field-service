from odoo import api, fields, models, _

class FieldServiceOrderLineEmployee(models.Model):
    _name = 'fieldservice.order.line.employee'
    _description = 'Field Service Order Line Employee'

    fieldservice_order_line_id = fields.Many2one('fieldservice.order.line', string='Field Service Order Line')
    employee_id = fields.Many2one('hr.employee', string='Employee')

