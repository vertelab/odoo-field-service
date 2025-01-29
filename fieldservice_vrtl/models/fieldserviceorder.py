from odoo import api, fields, models

class FieldServiceOrder(models.Model):
    _name = 'fieldservice.order'
    _description = 'Field Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('fieldservice.order'))
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
    duration = fields.Float(string='Duration', compute='_compute_duration', store=True)

    order_line_ids = fields.One2many('fieldservice.order.line', 'order_id', string='Order Lines')

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for order in self:
            if order.date_start and order.date_end:
                duration = (order.date_end - order.date_start).total_seconds() / 3600
                order.duration = round(duration, 2)
            else:
                order.duration = 0.0

    @api.model
    def _read_group_stage_ids(self, stages = False, domain = False, order = False):
        stage_ids = self.env['fieldservice.stage'].search([])
        return stage_ids

class FieldServiceOrderLine(models.Model):
    _name = 'fieldservice.order.line'
    _description = 'Field Service Order Line'

    order_id = fields.Many2one('fieldservice.order', string='Service Order', required=True)
    stage_id = fields.Many2one('fieldservice.stage', string='Stage', tracking=True)
    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date')
    image_ids = fields.Many2many('ir.attachment', string='Images')

    def open_form_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fieldservice.order.line',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

class FieldServiceStage(models.Model):
    _name = 'fieldservice.stage'
    _description = 'Field Service Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    fold = fields.Boolean(string='Folded in Kanban')
    is_closed = fields.Boolean(string='Closed Stage')
    description = fields.Text(translate=True)
    mail_template_id = fields.Many2one('mail.template', string='Email Template')
    sms_template_id = fields.Many2one('sms.template', string='SMS Template')
