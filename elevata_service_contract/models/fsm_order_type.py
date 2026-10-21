from odoo import fields, models


class FSMOrderType(models.Model):
    _inherit = 'fieldservice.order.type'

    use_service_checklist = fields.Boolean(
        string='Generera servicechecklista',
        help='Skapar hissens servicechecklista automatiskt på arbetsorder '
             'av denna typ när hissen kräver checklista.',
    )
