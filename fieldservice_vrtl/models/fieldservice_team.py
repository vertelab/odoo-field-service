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


class FieldserviceTeam(models.Model):
    """A field service team.

    A team is deliberately open-ended: it can stand for a work crew, a
    vehicle with its crew, a competence group, or a single technician.
    The only thing the model guarantees is that a team has members and,
    optionally, someone who owns its planning calendar.

    Integrations live in bridge modules (e.g. ``fieldservice_fleet_vrtl``
    for vehicles) so that this model stays free of optional dependencies.
    """

    _name = 'fieldservice.team'
    _description = 'Field Service Team'
    _order = 'sequence, name'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of teams in lists. Lower comes first.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to archive the team instead of deleting it.',
    )
    color = fields.Char(
        string='Color',
        default='#3498DB',
        help='Hex colour used to tell teams apart in lists and kanban.',
    )

    leader_id = fields.Many2one(
        'hr.employee',
        string='Team Leader',
        ondelete='set null',
        help='Technician responsible for the team.',
    )
    member_ids = fields.Many2many(
        'hr.employee',
        'fieldservice_team_hr_employee_rel',
        'team_id',
        'employee_id',
        string='Members',
        help='Technicians that belong to the team.',
    )
    member_count = fields.Integer(
        string='Member Count',
        compute='_compute_member_count',
    )

    calendar_user_id = fields.Many2one(
        'res.users',
        string='Planning Calendar Owner',
        ondelete='set null',
        domain=[('share', '=', False)],
        help='User whose calendar receives the planning events for this '
             'team. Leave empty to fall back to the company default.',
    )

    order_ids = fields.One2many(
        'fieldservice.order',
        'team_id',
        string='Orders',
    )
    order_count = fields.Integer(
        string='Order Count',
        compute='_compute_order_count',
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )

    # ── Computes ──

    @api.depends('member_ids')
    def _compute_member_count(self):
        for team in self:
            team.member_count = len(team.member_ids)

    def _compute_order_count(self):
        # Grouped read: one query for the whole recordset.
        counts = dict(
            self.env['fieldservice.order']._read_group(
                [('team_id', 'in', self.ids)],
                groupby=['team_id'],
                aggregates=['__count'],
            )
        ) if self.ids else {}
        for team in self:
            team.order_count = counts.get(team, 0)

    # ── Helpers ──

    def _get_calendar_user(self):
        """Return the user that should own this team's planning events.

        Resolution order:
          1. the team's own calendar owner,
          2. the company default,
          3. the current user.

        Never returns an empty recordset, so callers can rely on it.
        """
        self.ensure_one()
        return (
            self.calendar_user_id
            or self.company_id.fsm_calendar_user_id
            or self.env.user
        )

    def _get_planning_partner_ids(self):
        """Partners that should attend a planning event for this team.

        Every member with a user account becomes an attendee, so a
        technician sees the event even when they do not own it.
        """
        self.ensure_one()
        return self.member_ids.mapped('user_id.partner_id')

    def name_get(self):
        # Show the leader in the display name so two teams called
        # "Team 1" from different companies stay distinguishable.
        result = []
        for team in self:
            name = team.name
            if team.leader_id:
                name = '%s (%s)' % (name, team.leader_id.name)
            result.append((team.id, name))
        return result
