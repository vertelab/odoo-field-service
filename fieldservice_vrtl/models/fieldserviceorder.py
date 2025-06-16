from odoo import api, fields, models, _
from datetime import date as date_type
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class FieldServiceOrder(models.Model):
    _name = 'fieldservice.order'
    _description = 'Field Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'project.task': 'task_id'}

    task_id = fields.Many2one('project.task', required=True, ondelete="cascade")

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
    stage_id = fields.Many2one(
        'fieldservice.stage', string='Stage', tracking=True, group_expand='_read_group_stage_ids',
        default=lambda self: self.env['fieldservice.stage'].search([], limit=1)
    )
    field_service_order_tag_ids = fields.Many2many('field.service.order.tag', string="Tag")
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

    work_instructions = fields.Html(string='Work Instructions')
    location_instructions = fields.Text(string='Location Instructions')

    product_type = fields.Many2one('fieldservice.order.type', string= 'Product Type')
    date_start = fields.Datetime(string='Actual Start',compute="compute_date_start_end",store=True,readonly=False)
    date_end = fields.Datetime(string='Actual End',compute="co mpute_date_start_end",store=True,readonly=False)
   
    # time_until_work_start = fields.Float(string='Time until work start', compute='_compute_time_until_work_start', store=True, help='Time in hours')
    # time_until_work_start_avg = fields.Float(group_operator='avg', string='Time until work start (AVG)', compute='_compute_time_until_work_start', store=True, help='Time in hours')
    # time_until_work_done = fields.Float(string='Time until work done', compute='_compute_time_until_work_done', store=True, help='Time in hours')
    # time_until_work_start_max = fields.Float(group_operator="max", string='Time until work start (MAX)', compute='_compute_time_until_work_start', store=True, help='Time in hours')
    # time_until_work_done_avg = fields.Float(group_operator='avg', string='Time until work done (AVG)', compute='_compute_time_until_work_done', store=True, help='Time in hours')
    partner_id = fields.Many2one('res.partner', string="Partner",)

    @api.depends('stage_id')
    def compute_date_start_end(self):
        
        for order in self:
            if not order.date_start and order.stage_id.type == "start":
                order.date_start = fields.Datetime.now()
   

            elif not order.date_end and order.stage_id.type == "end":
                order.date_end = fields.Datetime.now()

    order_line_ids = fields.One2many('fieldservice.order.line', 'order_id', string='Order Lines')
    stakeholder_ids = fields.One2many('fieldservice.stakeholder', 'order_id', string='Stakeholders', ondelete='cascade')
    create_date = fields.Datetime(readonly=True)

    #Object description
    brand = fields.Many2one("product.brand", string="Brand", help="Select a brand for this product")
    brand_logo = fields.Binary(related='brand.logo', string='Brand', readonly=True)
    #brand = fields.Char(string='Brand', help="The manufacturer or brand of the product")
    model = fields.Char(string='Model', help="The model name or number of the product")
    serial_number = fields.Char(string='Serial Number', help="The unique serial number of the product")
    product_number = fields.Char(string='Product Number', help="The product number or part number")
    marking = fields.Char(string='Marking', help="Any specific marking or label on the product")
    purchase_date = fields.Date(string='Purchase Date', help="The date when the product was purchased")
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    def create_or_set_product(self):
        for order in self:
            product_tmpl = self.env['product.template'].search([
            ('product_number','=',order.product_number),
            ('product_type','=',order.product_type),
            ('brand','=',order.brand),
            ('model','=',order.model),
            ])
            if product_tmpl:
               order.product_tmpl_id = product_tmpl
            else:
                order.product_tmpl_id = self.env['product.template'].create({
                'product_number':order.product_number,
                'product_type':order.product_type,
                'brand':order.brand,
                'model':order.model,
                })
    #ocassion count
    line_count = fields.Integer(string='Occasion Count', compute='_compute_line_count', store = True)
    line_count_avg = fields.Integer(aggregator='avg', string='Occasion Count (AVG)', compute='_compute_line_count',
                                    store=True)
    total_duration = fields.Float(string='Total Duration', compute='_compute_total_duration', store=True,
                                  help='Total duration of all lines', aggregator=False)


    @api.depends('order_line_ids.duration')
    def _compute_total_duration(self):
        for record in self:
            record.total_duration = sum(line.duration for line in record.order_line_ids)


    @api.depends('order_line_ids')
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.order_line_ids)
            record.line_count_avg = record.line_count

    api.depends()          
    def create_occasion(self):
        record = self.env['fieldservice.order.line'].create([{'order_id':self.id,'date_start':self.planned_start_datetime}])
        return record.open_planning_view()
    
    # @api.depends('create_date', 'date_start')
    # def _compute_time_until_work_start(self):
    #     for record in self:
    #         if record.create_date and record.date_start:
    #             record.time_until_work_start = (record.date_start - record.create_date).total_seconds() / 3600
    #         else:
    #             record.time_until_work_start = 0.0
    #         record.time_until_work_start_avg = record.time_until_work_start
    #         record.time_until_work_start_max = record.time_until_work_start

    @api.model_create_multi
    def create(self, vals_list):
        default_project_id = int(self.env['ir.config_parameter'].sudo().get_param('fieldservice.default_project_id') or 0)
        for vals in vals_list:
            # Generate order number if needed
            if vals.get('order_number', _('New')) == _('New'):
                new_number = self.env['ir.sequence'].next_by_code('fieldservice.order')
                vals['order_number'] = new_number or _('New')
            # Create the related project.task
            task_vals = {
                'name': vals.get('name', 'New Task'),
                'project_id':default_project_id,
            }
            task = self.env['project.task'].create(task_vals)
            vals['task_id'] = task.id
            _logger.info(f"Final vals for creation: {vals}")

        res = super(FieldServiceOrder, self).create(vals_list)
        # If you have a method to call after creation, call it for each record
        res.create_occasion()
        return res

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
    
    def create_occasion(self):
        record = self.env['fieldservice.order.line'].create([{'order_id':self.id,'date_start':self.planned_start_datetime, 'date_end': self.planned_start_datetime}])
        return record.open_planning_view()

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
