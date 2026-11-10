from odoo import models, fields, _


class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'

    maintenance_request_id = fields.Many2one(
        'maintenance.request',
        string='Maintenance Request',
        copy=False,
        ondelete='set null',
        index=True,
        help='The maintenance request this order was created from.',
    )
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipment',
        index=True,
        help='The asset the technician is working on.',
    )

    def action_view_maintenance_request(self):
        self.ensure_one()
        return {
            'name': _('Maintenance Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'res_id': self.maintenance_request_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
