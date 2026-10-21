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

from odoo import fields, models


class FieldserviceTeam(models.Model):
    _inherit = 'fieldservice.team'

    vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        'fieldservice_team_fleet_vehicle_rel',
        'team_id',
        'vehicle_id',
        string='Vehicles',
        help='Vehicles used by the team. A team may have several, e.g. a '
             'van and a service cart.',
    )
    vehicle_count = fields.Integer(
        string='Vehicle Count',
        compute='_compute_vehicle_count',
    )

    def _compute_vehicle_count(self):
        for team in self:
            team.vehicle_count = len(team.vehicle_ids)
