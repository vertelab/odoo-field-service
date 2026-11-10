# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    """Order history on the asset.

    A technician arriving at an asset wants to know what was done last time
    and whether something is still outstanding. The count is what the smart
    button shows; the list is what it opens.
    """

    _inherit = 'maintenance.equipment'

    fsm_order_ids = fields.One2many(
        'fieldservice.order',
        'equipment_id',
        string='Order History',
    )
    active_order_count = fields.Integer(
        string='Active Orders',
        compute='_compute_active_order_count',
        store=True,
        help='Stored so it can be searched and grouped: "which assets have '
             'open work?" is a question a planner asks every morning.',
    )

    @api.depends('fsm_order_ids', 'fsm_order_ids.stage_id')
    def _compute_active_order_count(self):
        # is_closed lives on fieldservice.stage, not on the order. The
        # dependency has to name the path, or the count does not recompute
        # when an order moves to a closed stage.
        for equipment in self:
            equipment.active_order_count = len(
                equipment.fsm_order_ids.filtered(lambda o: not o.stage_id.is_closed)
            )

    def action_view_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Order History'),
            'res_model': 'fieldservice.order',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
            'target': 'current',
        }
