from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)
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

    def get_planned_hours(self, domain):
        domain_copy = domain.copy()
        domain_copy.append(('employee_id', '=', self.id))

        line_employees = self.env['fieldservice.order.line.employee'].search(domain_copy)
        _logger.warning(f"{domain_copy=}")
        _logger.warning(f"{line_employees.employee_id.name=}")
        _logger.warning(f"{line_employees.fieldservice_order_line_id=}")
        _logger.warning(f"{line_employees.fieldservice_order_line_id.duration=}")
        total_duration = sum(line_employees.mapped('fieldservice_order_line_id.duration'))
        return total_duration
        #self = t,ex Sarah


