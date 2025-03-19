from odoo import api, fields, models, _
from datetime import date as date_type
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class FieldServiceOrder(models.Model):
    _name = 'fieldservice.order'
    _description = 'Field Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, readonly=False)
    order_number = fields.Char(string="Reference Number", default=lambda self: _('New'), readonly=True, copy=False, required = True)
    description = fields.Text(string='Problem Description')
    resolution = fields.Text(string='Resolution')
    reporter = fields.Many2one(comodel_name="res.partner", compute="_compute_reporter", store=True)
    address = fields.Char(related="reporter.street", store=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1')
    stage_id = fields.Many2one('fieldservice.stage', string='Stage', tracking=True,
                               group_expand='_read_group_stage_ids', default=lambda self: self.env['fieldservice.stage'].search([], limit=1))
    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        required=True, 
        default=lambda self: self.env.company
    )
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
    
    ##Object description
    brand = fields.Char(string='Brand', help="The manufacturer or brand of the product")
    model = fields.Char(string='Model', help="The model name or number of the product")
    serial_number = fields.Char(string='Serial Number', help="The unique serial number of the product")
    product_number = fields.Char(string='Product Number', help="The product number or part number")
    marking = fields.Char(string='Marking', help="Any specific marking or label on the product")
    purchase_date = fields.Date(string='Purchase Date', help="The date when the product was purchased")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            _logger.info(f"Creating order with initial vals: {vals}")
            if vals.get('order_number', _('New')) == _('New'):
                new_number = self.env['ir.sequence'].next_by_code('fieldservice.order')
                _logger.info(f"Generated new number: {new_number}")
                vals['order_number'] = new_number or _('New')
            _logger.info(f"Final vals for creation: {vals}")
        return super(FieldServiceOrder, self).create(vals_list)

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for order in self:
            if order.date_start and order.date_end:
                duration = (order.date_end - order.date_start).total_seconds() / 3600
                order.duration = round(duration, 2)
            else:
                order.duration = 0.0

    @api.depends("stakeholder_ids")
    def _compute_reporter(self):
        for record in self:
            stakeholder_ids = list(filter(lambda stakeholder_id: stakeholder_id.partner_status == "reporter",record.stakeholder_ids))
            _logger.error(f"{stakeholder_ids=}")
            if stakeholder_ids:
                record.reporter = stakeholder_ids[0].partner_id
            else:
                record.reporter = False


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

