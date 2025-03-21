from odoo import models, fields, api, _

class FieldServiceOrderLine(models.Model):
    _inherit = "fieldservice.order.line"

    timesheet_ids = fields.One2many('account.analytic.line', 'fieldservice_order_line_id', 'Associated Timesheets')
    fieldservice_order_line_employee_ids = fields.One2many('fieldservice.order.line.employee', 'fieldservice_order_line_id', ondelete='cascade', string='Employees')
    name = fields.Char(compute="compute_name", store=True, readonly=True)
    

    @api.depends('order_id.name', 'date_start')
    def compute_name(self):
        for record in self:
            record.name = f"{record.order_id.name} - {record.date_start}"


    @api.model_create_multi
    def create(self, vals_list):
        res = super(FieldServiceOrderLine, self).create(vals_list)
        for record in res:
            self.env['fieldservice.order.line.employee'].create({
                    'fieldservice_order_line_id': record.id,
                    'employee_id': False,  
                    'description': 'Empty Slot',
                })
        return res
