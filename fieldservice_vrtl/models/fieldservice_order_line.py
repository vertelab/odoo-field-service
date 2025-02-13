from odoo import api, fields, models

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
