from odoo import fields, models, _, api

class FieldServiceOrderLineEmployee(models.Model):
    _name = 'fieldservice.order.line.employee'
    _description = 'Field Service Order Line Employee'


    fieldservice_order_line_id = fields.Many2one('fieldservice.order.line', required=True)
    employee_id = fields.Many2one('hr.employee', required=True)
    # order_ids = fields.One2many('fieldservice.order.line','order_id', string='Service Order', required=True)
    description = fields.Text(string='Description')
    name = fields.Char(compute="compute_name", store=True, readonly=False)
    

    @api.depends('employee_id', 'employee_id.name')
    def compute_name(self):
        for record in self:
            record.name = f"{record.employee_id.name}"

