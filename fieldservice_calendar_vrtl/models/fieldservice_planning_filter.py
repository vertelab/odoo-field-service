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


class FieldservicePlanning(models.Model):
    """Team checkbox in the calendar sidebar.

    Kept in its own file so the field survives edits to
    fieldservice_planning.py — that file has been reverted twice by a
    checkout in the deploy directory.
    """

    _inherit = 'fieldservice.planning'

    team_checked = fields.Boolean(
        string='Team Checked',
        compute='_compute_team_checked',
        search='_search_team_checked',
        help='Whether this team is ticked in the calendar filter for the '
             'current user. Drives the checkbox list in the calendar view; '
             'the value is stored per user in calendar.filters.team.',
    )

    @api.depends('team_id')
    @api.depends_context('uid')
    def _compute_team_checked(self):
        """Look up the current user's checkbox for each team.

        A team with no stored filter row counts as checked — a new team
        must not silently disappear from the calendar the first time
        someone opens it.
        """
        Filter = self.env['calendar.filters.team']
        team_ids = [line.team_id.id for line in self if line.team_id]
        checked = {}
        if team_ids:
            rows = Filter.search([
                ('user_id', '=', self.env.user.id),
                ('team_id', 'in', team_ids),
            ])
            checked = {row.team_id.id: row.team_checked for row in rows}
        for line in self:
            line.team_checked = checked.get(line.team_id.id, True)

    def _search_team_checked(self, operator, value):
        """Let a domain search narrow on the same flag."""
        if operator not in ('=', '!='):
            raise ValueError(
                'Unsupported operator on team_checked: %s' % operator)
        checked = bool(value) if operator == '=' else not bool(value)
        rows = self.env['calendar.filters.team'].search([
            ('user_id', '=', self.env.user.id),
        ])
        hidden = rows.filtered(lambda r: r.team_checked != checked).team_id.ids
        return [('team_id', 'not in', hidden)]
