from odoo import models, fields, api, _

class FieldServiceOrderLine(models.Model):
    _inherit = "fieldservice.order.line"

    timesheet_ids = fields.One2many('account.analytic.line', 'fieldservice_order_line_id', 'Associated Timesheets')
    fieldservice_order_line_employee_ids = fields.One2many('fieldservice.order.line.employee', 'fieldservice_order_line_id', string='Employees')
    name = fields.Char(compute="compute_name", store=True, readonly=True)
    

    @api.depends('order_id.name', 'date_start')
    def compute_name(self):
        for record in self:
            record.name = f"{record.order_id.name} - {record.date_start}"
