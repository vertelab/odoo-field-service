from odoo import fields, models, _, api

class FieldServiceOrderLineEmployee(models.Model):
    _name = 'fieldservice.order.line.employee'
    _description = 'Field Service Order Line Employee'


    fieldservice_order_line_id = fields.Many2one('fieldservice.order.line', required=True)
    employee_id = fields.Many2one('hr.employee', required=True)
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

    @api.depends('employee_id', 'employee_id.name')
    def compute_name(self):
        for record in self:
            record.name = f"{record.employee_id.name}"

    # @api.depends('name', 'user_id.avatar_1024', 'image_1024')
    # def _compute_avatar_1024(self):
    #     super()._compute_avatar_1024()

    # @api.depends('name', 'user_id.avatar_128', 'image_128')
    # def _compute_avatar_128(self):
    #     super()._compute_avatar_128()