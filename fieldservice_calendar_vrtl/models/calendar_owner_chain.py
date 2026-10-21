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
    """Team gets a department, so the owner chain has a middle step."""

    _inherit = 'fieldservice.team'

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Department the team belongs to. Used to find a calendar '
             'owner when the team has none of its own.',
    )

    def _get_calendar_user(self):
        """Owner for this team: own owner, then department, then company.

        Overrides fieldservice_vrtl's team -> company chain to insert the
        department level. Still never empty.
        """
        self.ensure_one()
        if self.calendar_user_id:
            return self.calendar_user_id
        if self.department_id:
            user = self.department_id._get_fsm_calendar_user()
            if user:
                return user
        company = self.company_id or self.env.company
        if company.fsm_calendar_user_id:
            return company.fsm_calendar_user_id
        return self.env['res.users']


class FieldservicePlanningOwner(models.Model):
    """Owner chain for a planning line, with all four levels.

    company -> department -> team -> individual. The individual level is
    the technician's own user, used only when nothing above resolves.
    """

    _inherit = 'fieldservice.planning'

    def _get_calendar_user(self):
        self.ensure_one()
        team = self.team_id or self.fsm_order_id._get_planning_team()
        if team:
            user = team._get_calendar_user()
            if user:
                return user
        tech = self.requested_employee_ids
        if tech.user_id:
            return tech.user_id
        return self.env.user
