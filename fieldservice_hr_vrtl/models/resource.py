# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    field_service_id = fields.Many2one("fieldservice.order", string='Field Service Order')
    field_service_employee_line_id = fields.Many2one("fieldservice.order.line.employee", string='Field Service Order')

    @api.constrains('date_from', 'date_to', 'calendar_id')
    def _check_compare_field_dates(self):
        all_existing_field_service_order = self.env['resource.calendar.leaves'].search([
            ('resource_id', '=', False),
            ('company_id', 'in', self.company_id.ids),
            ('date_from', '<=', max(self.mapped('date_to'))),
            ('date_to', '>=', min(self.mapped('date_from'))),
        ])
        for record in self:
            if not record.resource_id:
                existing_field_service_orders = all_existing_field_service_order.filtered(lambda field_service_order:
                        record.id != field_service_order.id
                        and record['company_id'] == field_service_order['company_id']
                        and record['date_from'] <= field_service_order['date_to']
                        and record['date_to'] >= field_service_order['date_from'])
                if record.calendar_id:
                    existing_field_service_orders = existing_field_service_orders.filtered(lambda l: not l.calendar_id or l.calendar_id == record.calendar_id)
                if existing_field_service_orders:
                    raise ValidationError(_('Two public holidays cannot overlap each other for the same working hours.'))
