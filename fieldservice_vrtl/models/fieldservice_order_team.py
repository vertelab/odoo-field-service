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

from odoo import _, api, fields, models


class FieldserviceOrder(models.Model):
    _inherit = 'fieldservice.order'

    # Defined here rather than in fieldservice_maintenance: the analytic
    # compute in fieldservice_account_analytic depends on this field but
    # that module does not declare the dependency that defines it, so the
    # registry fails to load unless the field exists before that module is
    # loaded. fieldservice_maintenance inherits the same definition.
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipment',
        index=True,
        help='The asset the technician is working on.',
    )

    team_id = fields.Many2one(
        'fieldservice.team',
        string='Team',
        ondelete='set null',
        index=True,
        help='Team responsible for the order. Optional: an order can be '
             'assigned to individual technicians instead.',
    )

    def _get_planning_team(self):
        """Return the team whose calendar should hold this order's events.

        Falls back to the team of the assigned technician when the order
        itself has no team, so a single-technician order still lands in
        the right calendar.
        """
        self.ensure_one()
        if self.team_id:
            return self.team_id
        return self.requested_employee_ids.mapped('team_ids')[:1]
