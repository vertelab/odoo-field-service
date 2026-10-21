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


class HrDepartment(models.Model):
    """Department as a calendar level.

    Company and team already had a calendar owner; department did not, so
    the middle of the four levels (company / department / team /
    individual) had nowhere to live.
    """

    _inherit = 'hr.department'

    fsm_calendar_user_id = fields.Many2one(
        'res.users',
        string='Field Service Calendar Owner',
        domain="[('share', '=', False)]",
        help='Owner of planning events for this department. Used when the '
             'team has no calendar owner of its own.',
    )
    fieldservice_team_ids = fields.One2many(
        'fieldservice.team',
        'department_id',
        string='Field Service Teams',
    )

    def _get_fsm_calendar_user(self):
        """Owner for this department, walking up the parent chain.

        A sub-department without its own owner inherits the parent's — the
        same way a team falls back to its company.
        """
        self.ensure_one()
        department = self
        while department:
            if department.fsm_calendar_user_id:
                return department.fsm_calendar_user_id
            department = department.parent_id
        return self.env['res.users']


class HrEmployee(models.Model):
    """Technicians need a partner to be calendar participants.

    calendar.event.partner_ids is a many2many on res.partner. Employees
    without a user account had no partner at all, so 11 of 12 technicians
    could not be added to an event even as a participant. The partner is
    created on demand and kept separate from user_id: a technician can be
    on the calendar without being able to log in.
    """

    _inherit = 'hr.employee'

    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        compute='_compute_partner_id',
        store=True,
        readonly=False,
        help='Partner used when this employee is a calendar participant. '
             'Taken from the linked user when there is one; otherwise a '
             'contact is created so the technician can still appear on the '
             'planning calendar.',
    )

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_partner_id(self):
        for employee in self:
            employee.partner_id = employee.user_id.partner_id or employee.partner_id

    def _get_calendar_partner(self):
        """Return the partner to put on a calendar event, creating one.

        Never returns an empty recordset: a technician without a user
        account still has to be visible as a participant.
        """
        self.ensure_one()
        if self.partner_id:
            return self.partner_id
        partner = self.env['res.partner'].create({
            'name': self.name,
            'email': self.work_email or False,
            'phone': self.work_phone or False,
            'company_id': self.company_id.id or self.env.company.id,
        })
        self.partner_id = partner
        return partner
