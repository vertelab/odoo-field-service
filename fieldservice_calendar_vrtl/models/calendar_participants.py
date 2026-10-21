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

from odoo import models


class FieldservicePlanningParticipants(models.Model):
    """Technicians become participants, not owners.

    The base code built the participant list from tech.user_id.partner_id,
    which is empty for every technician without a user account — 11 of 12
    in the current data. Those technicians were dropped from the event
    silently. _get_calendar_partner() creates a contact when needed, so
    everyone requested on the order is actually on the calendar.
    """

    _inherit = 'fieldservice.planning'

    def _get_participant_partners(self):
        """Partners for every requested technician plus the customer."""
        self.ensure_one()
        partners = self.env['res.partner']
        for employee in self.requested_employee_ids:
            partners |= employee._get_calendar_partner()
        order = self.fsm_order_id
        if order.partner_id:
            partners |= order.partner_id
        return partners

    def _prepare_calendar_event_vals(self):
        vals = super()._prepare_calendar_event_vals()
        partners = self._get_participant_partners()
        vals['partner_ids'] = [(6, 0, partners.ids)]
        return vals
