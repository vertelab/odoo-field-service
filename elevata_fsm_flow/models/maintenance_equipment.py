# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class MaintenanceEquipment(models.Model):
    """Field service links on the elevator.

    The OCA fsm.location carried the order count and the "view orders"
    action. With the elevator as maintenance.equipment, that belongs here.
    """

    _inherit = 'maintenance.equipment'

    fsm_order_count = fields.Integer(
        string='Work Orders',
        compute='_compute_fsm_order_count',
    )

    @api.depends('is_elevator')
    def _compute_fsm_order_count(self):
        Order = self.env['fieldservice.order']
        for equipment in self:
            if not equipment.is_elevator:
                equipment.fsm_order_count = 0
                continue
            equipment.fsm_order_count = Order.search_count([
                ('equipment_id', '=', equipment.id),
                ('stage_id.is_closed', '=', False),
            ])

    def action_view_fsm_orders(self):
        """Smart button: open work orders on this elevator."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Orders — %s') % (self.elevator_number or self.name),
            'res_model': 'fieldservice.order',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }
