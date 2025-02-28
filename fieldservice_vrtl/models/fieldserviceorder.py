from odoo import api, fields, models, _
from datetime import date as date_type
from datetime import datetime, timedelta

class FieldServiceOrder(models.Model):
    _name = 'fieldservice.order'
    _description = 'Field Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, readonly=False)
    description = fields.Text(string='Problem Description')
    resolution = fields.Text(string='Resolution')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1')
    stage_id = fields.Many2one('fieldservice.stage', string='Stage', tracking=True,
                               group_expand='_read_group_stage_ids', default=lambda self: self.env['fieldservice.stage'].search([], limit=1))
    
    planned_start_datetime = fields.Datetime(string='Planned Start')
    deadline_datetime = fields.Datetime(string='Deadline')
    planned_duration = fields.Float(string='Planned Duration', help='Duration in hours')
    requested_employee_ids = fields.Many2many('hr.employee', string='Requested Employees')

    work_instructions = fields.Text(string='Work Instructions')
    location_instructions = fields.Text(string='Location Instructions')

    date_start = fields.Datetime(string='Actual Start')
    date_end = fields.Datetime(string='Actual End')

    partner_id = fields.Many2one('res.partner', string="Partner",)
    # partner_status = fields.Selection([('legal_owner', 'Legal Owner'),
    #                                    ], string="Status", default='legal_owner')


    order_line_ids = fields.One2many('fieldservice.order.line', 'order_id', string='Order Lines')
    stakeholder_ids = fields.One2many('fieldservice.stakeholder', 'order_id', string='Stakeholders')

    # @api.depends('date_start', 'date_end')
    # def _compute_duration(self):
    #     for order in self:
    #         if order.date_start and order.date_end:
    #             duration = (order.date_end - order.date_start).total_seconds() / 3600
    #             order.duration = round(duration, 2)
    #         else:
    #             order.duration = 0.0

    
    @api.onchange("order_line_ids")
    def set_start_date(self):
        for line in self.order_line_ids:
            if not line.date_start:
                line.date_start = fields.Datetime.now()
            if not self.date_start:
                earliest_date = min((line.date_start.date() for line in 
                                     self.order_line_ids if line.date_start), default=None)
                if earliest_date:
                    self.date_start = earliest_date

   


    @api.model
    def _read_group_stage_ids(self, stages = False, domain = False, order = False):
        stage_ids = self.env['fieldservice.stage'].search([])
        return stage_ids


    def open_order_lines_calendar(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name' : 'Field Service Order Lines',
            'res_model': 'fieldservice.order.line',
            #'res_id': self.id,
            'view_mode': 'calendar,list,form,kanban',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
            'target': 'current',
        }

    def open_order_lines_kanban(self):

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Field Service Order Lines',
            'res_model': 'fieldservice.order.line',
            'view_mode': 'kanban,list,form,calendar',
            'domain': [('order_id', '=', self.id)],
            'context': {
                'default_order_id': self.id,
                'group_by': 'date_start:day'
            },
            'target': 'current',
        }
    




    # @api.depends('date_end')
    # def _compute_custom_state(self):
    #     today = fields.Date.today()
    #     for record in self:
    #         if record.date_end:
    #             days_until_due = (record.date_end.date() - today).days
    #             if days_until_due < 0:
    #                 record.custom_state = 'overdue'
    #             elif 0 <= days_until_due <= 5:
    #                 record.custom_state = 'due_soon'
    #             else:
    #                 record.custom_state = 'planned'
    #         else:
    #             record.custom_state = 'planned'       
    # 
    # @api.depends('date_end')
    # def _compute_custom_state(self):
    #     _logger.warning(f"{self.env.context=}")
    #     max_duration = 40
    #     for record in self:
    #         duration_for_day = self.env[]
