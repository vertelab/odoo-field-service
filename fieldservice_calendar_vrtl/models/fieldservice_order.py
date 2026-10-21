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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models


class FieldserviceOrder(models.Model):
    _inherit = 'fieldservice.order'

    planning_line_ids = fields.One2many(
        'fieldservice.planning',
        'fsm_order_id',
        string='Planning Lines',
    )
    planning_count = fields.Integer(
        string='Planning Count',
        compute='_compute_planning_count',
    )

    @api.depends('planning_line_ids')
    def _compute_planning_count(self):
        for order in self:
            order.planning_count = len(order.planning_line_ids)

    def action_view_planning_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Planning',
            'res_model': 'fieldservice.planning',
            'view_mode': 'list,form',
            'domain': [('fsm_order_id', '=', self.id)],
            'context': {'default_fsm_order_id': self.id},
        }

    def unlink(self):
        # The planning lines cascade at database level, which bypasses
        # fieldservice.planning.unlink() and would leave the calendar
        # events behind. Remove them explicitly first.
        self.mapped('planning_line_ids')._remove_calendar_event()
        return super().unlink()

    def action_plan_order(self):
        """Open a new planning line pre-filled from the order."""
        self.ensure_one()
        technician = self.requested_employee_ids[:1]
        team = self.team_id or self._get_planning_team()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Plan Work Order',
            'res_model': 'fieldservice.planning',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_fsm_order_id': self.id,
                'default_requested_employee_ids': technician.id or False,
                'default_team_id': team.id or False,
            },
        }
