from odoo import models, fields, api

class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'

    total_time_duration = fields.Float(string='Total Time Duration',compute='_compute_total_time_duration',store=True)

    @api.depends('order_line_ids.timesheet_ids.unit_amount')
    def _compute_total_time_duration(self):
        for record in self:
            record.total_time_duration = sum(
                record.order_line_ids.mapped('timesheet_ids').mapped('unit_amount')
            )
