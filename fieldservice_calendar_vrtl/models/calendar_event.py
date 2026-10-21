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

import pytz

from odoo import api, fields, models

NO_SYNC_BACK = 'no_calendar_sync_back'

# Tag name -> colour index. The names are the contract with the data file;
# the index drives the colour the calendar view paints.
TAG_COLORS = {
    'Planning Booked': 3,
    'Planning Not Booked': 2,
    'Timesheet': 1,
    'Locked Timesheet': 8,
}


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    fsm_order_id = fields.Many2one(
        'fieldservice.order',
        string='Work Order',
        ondelete='set null',
        copy=False,
        index=True,
    )
    fsm_planning_ids = fields.One2many(
        'fieldservice.planning',
        'calendar_event_id',
        string='Planning Lines',
    )
    fsm_color = fields.Integer(
        string='Field Service Colour',
        compute='_compute_fsm_color',
        store=True,
        default=0,
    )

    @api.depends('categ_ids', 'categ_ids.name')
    def _compute_fsm_color(self):
        for event in self:
            names = set(event.categ_ids.mapped('name'))
            event.fsm_color = next(
                (idx for name, idx in TAG_COLORS.items() if name in names), 0
            )

    @api.depends('categ_ids', 'categ_ids.name')
    def _compute_user_can_edit(self):
        super()._compute_user_can_edit()
        locked = self.env.ref(
            'fieldservice_calendar_vrtl.calendar_tag_locked_timesheet',
            raise_if_not_found=False,
        )
        if locked:
            for event in self:
                if locked in event.categ_ids:
                    event.user_can_edit = False

    @api.model
    def get_fsm_color_config(self):
        get = self.env['ir.config_parameter'].sudo().get_param
        return {
            '2': {
                'bg': get('fieldservice_calendar.color_planned_bg', '#27ae60'),
                'border': get('fieldservice_calendar.color_planned_border', '#1e8449'),
                'text': get('fieldservice_calendar.color_planned_text', '#ffffff'),
                'allBorder': False,
            },
            '3': {
                'bg': get('fieldservice_calendar.color_booked_bg', '#e74c3c'),
                'border': get('fieldservice_calendar.color_booked_border', '#a93226'),
                'text': get('fieldservice_calendar.color_booked_text', '#ffffff'),
                'allBorder': False,
            },
            '1': {
                'bg': get('fieldservice_calendar.color_timesheet_bg', '#95a5a6'),
                'border': get('fieldservice_calendar.color_timesheet_border', '#717d7e'),
                'text': get('fieldservice_calendar.color_timesheet_text', '#ffffff'),
                'allBorder': True,
            },
            '8': {
                'bg': get('fieldservice_calendar.color_locked_bg', '#bdc3c7'),
                'border': get('fieldservice_calendar.color_locked_border', '#95a5a6'),
                'text': get('fieldservice_calendar.color_locked_text', '#333333'),
                'allBorder': True,
            },
        }

    def _round_to_15min(self, float_time):
        return round(float_time * 4) / 4

    def _event_to_planning_vals(self, event):
        """Translate an event's start/stop into planning line values."""
        vals = {}
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        if event.start:
            local_start = pytz.UTC.localize(event.start).astimezone(user_tz)
            vals['planning_date'] = local_start.date()
            vals['time_start'] = self._round_to_15min(
                local_start.hour + local_start.minute / 60.0
            )
        if event.stop:
            local_stop = pytz.UTC.localize(event.stop).astimezone(user_tz)
            vals['time_end'] = self._round_to_15min(
                local_stop.hour + local_stop.minute / 60.0
            )
        return vals

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get(NO_SYNC_BACK):
            return res
        if 'start' not in vals and 'stop' not in vals:
            return res
        for event in self:
            planning_vals = self._event_to_planning_vals(event)
            if planning_vals and event.fsm_planning_ids:
                event.fsm_planning_ids.with_context(**{NO_SYNC_BACK: True}).write(
                    planning_vals
                )
        return res
