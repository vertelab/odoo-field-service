from odoo import models, fields, api, _

# class FieldServiceTimesheet(models.Model):
#     _name = 'custom.timesheet'
#     _description = 'Field Service Timesheet'
#     _inherit = ['mail.thread', 'mail.activity.mixin',]

#     name = fields.Char(string='Name', required=True)
#     employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
#     date = fields.Date(string='Date', required=True, default=fields.Date.today)
#     project_id = fields.Many2one('project.project', string='Project')
#     task_id = fields.Many2one('project.task', string='Task')
#     unit_amount = fields.Float(string='Duration', required=True)
#     description = fields.Text(string='Description')
    
#     @api.onchange('project_id')
#     def _onchange_project_id(self):
#         if self.project_id:
#             return {'domain': {'task_id': [('project_id', '=', self.project_id.id)]}}
#         return {'domain': {'task_id': []}}

class FieldServiceOrderLine(models.Model):
    _inherit = "fieldservice.order.line"

    timesheet_ids = fields.One2many('account.analytic.line', 
            'fieldservice_order_line_id', 'Associated Timesheets')
    

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    fieldservice_order_line_id = fields.Many2one('fieldservice.order.line')    