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


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    team_ids = fields.Many2many(
        'fieldservice.team',
        'fieldservice_team_hr_employee_rel',
        'employee_id',
        'team_id',
        string='Field Service Teams',
        help='Teams this technician belongs to.',
    )
    team_count = fields.Integer(
        string='Team Count',
        compute='_compute_team_count',
    )

    def _compute_team_count(self):
        for employee in self:
            employee.team_count = len(employee.team_ids)
