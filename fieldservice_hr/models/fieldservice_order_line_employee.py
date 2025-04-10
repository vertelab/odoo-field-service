from odoo import fields, models, _, api

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
    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if val.get('employee_id'):
                employee = self.env['hr.employee'].browse(int(val['employee_id']))
                if employee.exists() and employee.department_id:
                    val['hr_department_id'] = employee.department_id.id
                else:
                    val['hr_department_id'] = None 
        return super(FieldServiceOrderLineEmployee, self).create(vals_list)

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
