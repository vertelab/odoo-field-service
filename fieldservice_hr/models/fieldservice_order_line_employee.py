from odoo import fields, models, _, api
import logging

_logger = logging.getLogger(__name__)

class FieldServiceOrderLineEmployee(models.Model):
    _name = 'fieldservice.order.line.employee'
    _description = 'Field Service Order Line Employee'


    fieldservice_order_line_id = fields.Many2one('fieldservice.order.line', ondelete='cascade', required=True)
    employee_id = fields.Many2one(
        'hr.employee', required=False, domain="[('company_id', '=', company_id)]",
        group_expand='_read_group_employee_id',
    )

    hr_department_id = fields.Many2one(
        'hr.department', required=False, domain="[('company_id', '=', company_id)]",
         group_expand='_read_group_hr_department_id', readonly=False
    )

    # order_ids = fields.One2many('fieldservice.order.line','order_id', string='Service Order', required=True)
    address = fields.Char(related="employee_id.user_partner_id.street", store=True)
    priority = fields.Selection(related="fieldservice_order_line_id.priority")
    date_start = fields.Datetime(related="fieldservice_order_line_id.date_start")
    date_end = fields.Datetime(related="fieldservice_order_line_id.date_end")
    description = fields.Text(string='Description')
    name = fields.Char(compute="compute_name", store=True, readonly=False)

    image_1024 = fields.Image("Image 1024", related='employee_id.image_1024', compute_sudo=True)
    image_128 = fields.Image("Image 128", related='employee_id.image_128', compute_sudo=True)
    avatar_128 = fields.Image("Avatar 128", related='employee_id.avatar_128', compute_sudo=True)

    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        related="fieldservice_order_line_id.company_id"
    )

    # resource_calendar_id = fields.Many2one('resource.calendar', compute='_compute_resource_calendar_id', store=True, readonly=False, copy=False)

    # @api.depends('employee_id')
    # def _compute_resource_calendar_id(self):
    #     employees_by_dates = defaultdict(lambda: self.env['hr.employee'])
    #     for leave in self:
    #         if leave.employee_id and leave.request_date_from:
    #             employees_by_dates[leave.request_date_from] += leave.employee_id
    #             calendar_by_dates = {date_from: employees._get_calendars(date_from) for date_from, employees in employees_by_dates.items()}
    #     for leave in self:
    #         calendar = False
    #         if leave.employee_id and leave.request_date_from:
    #             calendar = calendar_by_dates[leave.request_date_from][leave.employee_id.id]
    #             leave.resource_calendar_id = calendar or self.env.company.resource_calendar_id

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if val.get('employee_id'):
                _logger.warning(f"har inget arbetsschema."*20)
                employee = self.env['hr.employee'].browse(int(val['employee_id']))
                if employee.exists() and employee.department_id:
                    val['hr_department_id'] = employee.department_id.id
                else:
                    val['hr_department_id'] = None 
                
        field_service_line_ids = super(FieldServiceOrderLineEmployee, self).create(vals_list)
        #for field_service in field_service_line_ids:
        field_service_line_ids._create_fieldservice_resource()
        return field_service_line_ids

    def write(self, values):
        res = super(FieldServiceOrderLineEmployee, self).write(values)
        if values.get('employee_id'):
            for record in self:
                if record.employee_id and record.employee_id.department_id:
                    record.hr_department_id = record.employee_id.department_id.id
                else:
                    record.hr_department_id = None
        return res




    @api.depends('employee_id', 'employee_id.name')
    def compute_name(self):
        for record in self:
            if record.employee_id:
                record.name = record.employee_id.name
            else:
                record.name = _("Unassigned Slot")

    def _read_group_employee_id(self, employee_id, domain):
        employee_ids = employee_id._search(domain)
        return employee_id.browse(employee_ids)

    def _read_group_hr_department_id(self, hr_department_id, domain):
        hr_department_ids = hr_department_id.sudo()._search(domain)
        return hr_department_id.browse(hr_department_ids)
    

    def _prepare_fieldservice_resource_vals(self):
        """Hook method for others to inject data
        """
        self.ensure_one()
        return {
            'name': _("%s: Field Service", self.employee_id.name),
            'date_from': self.date_start,
            'field_service_employee_line_id': self.id,
            'date_to': self.date_end,
            'resource_id': self.employee_id.resource_id.id,
            'calendar_id': self.employee_id.resource_calendar_id.id,
            'time_type': 'leave',
        }
    



    def _create_fieldservice_resource(self):
        """ This method will create entry in resource calendar time off object at the time of holidays validated
        :returns: created `resource.calendar.leaves`
        """
        vals_list = [leave._prepare_fieldservice_resource_vals() for leave in self]
        
        #_logger.warning(f"works good."*20)
        #_logger.warning(f"works good.{vals_list}")
        # if not vals_list.get('date_from'):
        #     return
        vals_list = list(filter(lambda _: _.get('date_from'), vals_list))
        _logger.warning(f"final works good.{vals_list}")
        if vals_list:
            return self.env['resource.calendar.leaves'].sudo().create(vals_list)

    def _remove_fieldservice_resource(self):
        """ This method will create entry in resource calendar time off object at the time of holidays cancel/removed """
        return self.env['resource.calendar.leaves'].search([('holiday_id', 'in', self.ids)]).unlink()
