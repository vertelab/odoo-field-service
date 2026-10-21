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

from datetime import datetime, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# Context key that stops the calendar event from syncing back into the
# planning line while the planning line is itself writing the event.
NO_SYNC_BACK = 'no_calendar_sync_back'


class FieldservicePlanning(models.Model):
    _name = 'fieldservice.planning'
    _description = 'Field Service Planning Line'
    _order = 'date_start, id'

    fsm_order_id = fields.Many2one(
        'fieldservice.order',
        string='Work Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    requested_employee_ids = fields.Many2one(
        'hr.employee',
        string='Technician',
        help='Technician assigned to this planning line. It may differ '
             'from the technicians on the order.',
    )
    team_id = fields.Many2one(
        'fieldservice.team',
        string='Team',
        help='Team that performs the work. Defaults to the team of the '
             'assigned technician.',
    )
    planning_date = fields.Date(string='Date', required=True)
    time_start = fields.Float(string='Start Time')
    time_end = fields.Float(string='End Time')
    date_start = fields.Datetime(
        string='Start',
        compute='_compute_datetime_fields',
        store=True,
        index=True,
    )
    date_stop = fields.Datetime(
        string='End',
        compute='_compute_datetime_fields',
        store=True,
    )
    duration = fields.Float(
        string='Duration',
        compute='_compute_datetime_fields',
        store=True,
        help='Duration in hours, derived from the start and end time.',
    )
    is_confirmed = fields.Boolean(
        string='Confirmed with Customer',
        default=False,
        help='Confirmed planning lines are shown in the "Planning Booked" '
             'colour; unconfirmed ones in "Planning Not Booked".',
    )
    note = fields.Char(string='Note')
    calendar_event_id = fields.Many2one(
        'calendar.event',
        string='Calendar Event',
        ondelete='set null',
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company',
        related='fsm_order_id.company_id',
        store=True,
        index=True,
    )

    # ── Compute ──

    @api.depends('planning_date', 'time_start', 'time_end')
    def _compute_datetime_fields(self):
        for rec in self:
            rec.date_start = False
            rec.date_stop = False
            rec.duration = 0.0
            if not rec.planning_date:
                continue
            if rec.time_start:
                rec.date_start = rec._float_time_to_utc(rec.time_start)
            if rec.time_end:
                rec.date_stop = rec._float_time_to_utc(rec.time_end)
            if rec.date_start and rec.date_stop:
                rec.duration = (rec.date_stop - rec.date_start).total_seconds() / 3600.0

    def _float_time_to_utc(self, float_time):
        """Turn a 8.5 style float time on planning_date into naive UTC.

        The float is read in the user's timezone, which is what the
        calendar week view shows, and stored as naive UTC, which is what
        calendar.event expects.
        """
        self.ensure_one()
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        base_date = datetime.combine(self.planning_date, datetime.min.time())
        hours = int(float_time)
        minutes = int(round((float_time % 1) * 60))
        local_dt = base_date + timedelta(hours=hours, minutes=minutes)
        return user_tz.localize(local_dt).astimezone(pytz.UTC).replace(tzinfo=None)

    @api.onchange('time_start', 'time_end', 'planning_date')
    def _onchange_planning_times(self):
        if self.planning_date and self.time_start and self.time_end:
            if self.time_start >= self.time_end:
                return {'warning': {
                    'title': _('Warning'),
                    'message': _('The start time must be before the end time.'),
                }}

    @api.onchange('requested_employee_ids')
    def _onchange_requested_employee_ids(self):
        if not self.team_id and self.requested_employee_ids:
            self.team_id = self.requested_employee_ids.team_ids[:1]

    @api.constrains('time_start', 'time_end')
    def _check_times(self):
        for rec in self:
            if rec.time_start and rec.time_end and rec.time_start >= rec.time_end:
                raise ValidationError(
                    _('The start time must be before the end time on %s.')
                    % (rec.fsm_order_id.name or '')
                )

    # ── Calendar event ──

    def _get_calendar_tag(self):
        self.ensure_one()
        xmlid = (
            'fieldservice_calendar_vrtl.calendar_tag_planned_booked'
            if self.is_confirmed
            else 'fieldservice_calendar_vrtl.calendar_tag_planned_unbooked'
        )
        return self.env.ref(xmlid, raise_if_not_found=False)

    def _get_calendar_user(self):
        """Resolve the owner of the calendar event.

        Order of preference: the team's calendar owner, then the company
        default, then the current user. Never empty — an event without an
        owner is invisible in the week view, which filters on user_id.
        """
        self.ensure_one()
        order = self.fsm_order_id
        team = self.team_id or order._get_planning_team()
        if team:
            user = team._get_calendar_user()
            if user:
                return user
        return self.env.user

    def _prepare_calendar_event_vals(self):
        self.ensure_one()
        order = self.fsm_order_id
        equipment_name = order.equipment_id.name if order.equipment_id else ''
        order_type = order.product_type.name if order.product_type else ''
        name_parts = [p for p in (order.name, order_type, equipment_name) if p]
        event_name = ' | '.join(name_parts) or _('Planned Order')

        # The technician is always a participant. The calendar owner is not
        # added here — the owner already sees the event through user_id, and
        # adding them as a participant would make them look like a technician.
        partner_ids = []
        tech = self.requested_employee_ids
        if tech.user_id.partner_id:
            partner_ids.append(tech.user_id.partner_id.id)

        tag = self._get_calendar_tag()
        status = _('Confirmed') if self.is_confirmed else _('Not confirmed')
        customer = order.partner_id.name or ''
        description = ' | '.join(p for p in (
            order.name or '',
            order_type,
            equipment_name,
            customer,
            tech.name or _('No technician'),
            status,
        ) if p)

        return {
            'name': event_name,
            'start': self.date_start,
            'stop': self.date_stop,
            'user_id': self._get_calendar_user().id,
            'partner_ids': [(6, 0, partner_ids)],
            'categ_ids': [(6, 0, [tag.id])] if tag else [(5, 0, 0)],
            'description': description,
            'fsm_order_id': order.id,
        }

    def _sync_to_calendar(self):
        for line in self:
            if not (line.date_start and line.date_stop):
                continue
            vals = line._prepare_calendar_event_vals()
            Event = self.env['calendar.event'].with_context(**{NO_SYNC_BACK: True})
            if line.calendar_event_id:
                line.calendar_event_id.with_context(**{NO_SYNC_BACK: True}).write(vals)
            else:
                line.calendar_event_id = Event.create(vals).id

    def _remove_calendar_event(self):
        for line in self:
            if line.calendar_event_id:
                line.calendar_event_id.with_context(**{NO_SYNC_BACK: True}).unlink()
                line.calendar_event_id = False

    # ── CRUD ──

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_to_calendar()
        return records

    def write(self, vals):
        res = super().write(vals)
        sync_fields = {
            'planning_date', 'time_start', 'time_end', 'requested_employee_ids',
            'team_id', 'is_confirmed', 'note', 'fsm_order_id',
        }
        if sync_fields & set(vals) and not self.env.context.get(NO_SYNC_BACK):
            self._sync_to_calendar()
        return res

    def unlink(self):
        self._remove_calendar_event()
        return super().unlink()


class FieldservicePlanningConvert(models.Model):
    """Bridge: turn a planning line into a timesheet line.

    Lives here rather than in the timesheet module so that the button in
    the order form always has a target. The actual timesheet model is
    optional — without hr_timesheet the button simply reports that the
    conversion is unavailable.
    """

    _inherit = 'fieldservice.planning'

    def action_convert_to_timesheet(self):
        self.ensure_one()
        if 'account.analytic.line' not in self.env:
            raise UserError(_(
                'Timesheets are not installed, so a planning line cannot be '
                'converted to reported hours.'
            ))
        if not self.requested_employee_ids:
            raise UserError(_(
                'Set a technician on the planning line before converting it '
                'to a timesheet.'
            ))
        Line = self.env['account.analytic.line']
        fsm_fields = set(Line._fields)
        vals = {
            'name': self.fsm_order_id.name or _('Field service work'),
            'date': self.planning_date or fields.Date.context_today(self),
        }
        if 'fsm_order_id' in fsm_fields:
            vals['fsm_order_id'] = self.fsm_order_id.id
        if 'employee_id' in fsm_fields:
            vals['employee_id'] = self.requested_employee_ids[:1].id
        if 'project_id' in fsm_fields and self.fsm_order_id.project_id:
            vals['project_id'] = self.fsm_order_id.project_id.id
        if 'unit_amount' in fsm_fields:
            vals['unit_amount'] = self.duration
        line = Line.create(vals)
        self.unlink()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'res_id': line.id,
            'view_mode': 'form',
            'target': 'current',
        }
