from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    fieldservice_order_line_employee_ids = fields.One2many('fieldservice.order.line.employee','employee_id',string='Employees')

    def open_form_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Field Service Order Employees',
            'res_model': 'fieldservice.order.line.employee',
            'view_mode': 'list,kanban',
            'target': 'new',
            'context': {'default_order_line_id': self.id},
        }
