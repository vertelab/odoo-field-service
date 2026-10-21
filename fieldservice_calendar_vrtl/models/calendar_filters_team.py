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


class CalendarFiltersTeam(models.Model):
    """Per-user checkbox state for the team filter in the calendar.

    Odoo's calendar view can render a checkbox per value of a many2one
    field (the `filters` attribute on a <field> in the calendar arch). For
    people it stores the state in calendar.filters, keyed on partner_id.
    That model cannot hold teams, so this is the same idea keyed on
    team_id.

    The view points at this model through write_model / write_field, and
    reads the checkbox back through filter_field — see
    views/fieldservice_planning_views.xml.
    """

    _name = 'calendar.filters.team'
    _description = 'Calendar Team Filters'
    _rec_name = 'team_id'

    user_id = fields.Many2one(
        'res.users',
        string='Me',
        required=True,
        default=lambda self: self.env.user,
        index=True,
        ondelete='cascade',
    )
    team_id = fields.Many2one(
        'fieldservice.team',
        string='Team',
        required=True,
        index=True,
        ondelete='cascade',
    )
    active = fields.Boolean(default=True)
    team_checked = fields.Boolean(
        string='Checked',
        default=True,
        help='Whether the team is ticked in the calendar filter for this user.',
    )

    _sql_constraints = [
        ('user_id_team_id_unique',
         'UNIQUE(user_id, team_id)',
         'A user cannot have the same team twice.'),
    ]

    @api.model
    def unlink_from_team_id(self, team_id):
        return self.search([('team_id', '=', team_id)]).unlink()
