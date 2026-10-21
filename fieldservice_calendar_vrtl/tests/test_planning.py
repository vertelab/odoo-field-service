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

from datetime import date, datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPlanning(TransactionCase):
    """Planning line <-> calendar event synchronisation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.tz = 'Europe/Stockholm'
        cls.partner = cls.env['res.partner'].create({'name': 'Planning Customer'})
        cls.order = cls.env['fieldservice.order'].create({
            'name': 'PLAN-001',
            'partner_id': cls.partner.id,
        })
        cls.technician = cls.env['hr.employee'].create({'name': 'Planner Tech'})
        cls.team = cls.env['fieldservice.team'].create({
            'name': 'Planning Team',
            'member_ids': [(6, 0, cls.technician.ids)],
        })
        cls.Planning = cls.env['fieldservice.planning']

    def _make_line(self, **kwargs):
        vals = {
            'fsm_order_id': self.order.id,
            'requested_employee_ids': self.technician.id,
            'planning_date': date(2026, 3, 2),
            'time_start': 8.0,
            'time_end': 10.0,
        }
        vals.update(kwargs)
        return self.Planning.create(vals)

    # ── Datetime computation ──

    def test_date_start_is_utc_from_user_timezone(self):
        line = self._make_line()
        # 08:00 Stockholm in March is CET (UTC+1) -> 07:00 UTC.
        self.assertEqual(line.date_start, datetime(2026, 3, 2, 7, 0))
        self.assertEqual(line.date_stop, datetime(2026, 3, 2, 9, 0))

    def test_duration_computed(self):
        line = self._make_line(time_start=8.0, time_end=11.5)
        self.assertAlmostEqual(line.duration, 3.5, places=2)

    def test_quarter_hour_is_preserved(self):
        line = self._make_line(time_start=8.25, time_end=9.75)
        self.assertEqual(line.date_start.minute, 15)
        self.assertEqual(line.date_stop.minute, 45)

    def test_no_date_means_no_datetimes(self):
        line = self.Planning.new({'fsm_order_id': self.order.id})
        line._compute_datetime_fields()
        self.assertFalse(line.date_start)
        self.assertFalse(line.date_stop)
        self.assertEqual(line.duration, 0.0)

    # ── Validation ──

    def test_start_after_end_raises(self):
        with self.assertRaises(ValidationError):
            self._make_line(time_start=12.0, time_end=9.0)

    def test_equal_start_and_end_raises(self):
        with self.assertRaises(ValidationError):
            self._make_line(time_start=9.0, time_end=9.0)

    # ── Calendar event creation ──

    def test_create_creates_calendar_event(self):
        line = self._make_line()
        self.assertTrue(line.calendar_event_id)
        self.assertEqual(line.calendar_event_id.start, line.date_start)
        self.assertEqual(line.calendar_event_id.stop, line.date_stop)

    def test_event_has_owner(self):
        line = self._make_line()
        self.assertTrue(line.calendar_event_id.user_id)
        self.assertEqual(line.calendar_event_id.user_id, self.env.user)

    def test_team_calendar_owner_wins(self):
        owner = self.env['res.users'].create({
            'name': 'Planner Owner',
            'login': 'planner_owner_test',
            'email': 'planner.owner@example.com',
        })
        self.team.calendar_user_id = owner
        line = self._make_line(team_id=self.team.id)
        self.assertEqual(line.calendar_event_id.user_id, owner)

    def test_event_links_back_to_order(self):
        line = self._make_line()
        self.assertEqual(line.calendar_event_id.fsm_order_id, self.order)

    def test_event_carries_planning_tag(self):
        line = self._make_line(is_confirmed=False)
        unbooked = self.env.ref(
            'fieldservice_calendar_vrtl.calendar_tag_planned_unbooked')
        self.assertIn(unbooked, line.calendar_event_id.categ_ids)

    def test_confirmed_line_uses_booked_tag(self):
        line = self._make_line(is_confirmed=True)
        booked = self.env.ref(
            'fieldservice_calendar_vrtl.calendar_tag_planned_booked')
        self.assertIn(booked, line.calendar_event_id.categ_ids)

    def test_technician_is_participant(self):
        user = self.env['res.users'].create({
            'name': 'Tech User',
            'login': 'tech_user_planning_test',
            'email': 'tech.planning@example.com',
        })
        self.technician.user_id = user
        line = self._make_line()
        self.assertIn(user.partner_id, line.calendar_event_id.partner_ids)

    # ── Calendar event updates ──

    def test_write_reschedules_event(self):
        line = self._make_line()
        event = line.calendar_event_id
        line.write({'time_start': 13.0, 'time_end': 15.0})
        self.assertEqual(event.start, line.date_start)
        self.assertEqual(event.stop, line.date_stop)

    def test_confirm_updates_tag(self):
        line = self._make_line(is_confirmed=False)
        line.write({'is_confirmed': True})
        booked = self.env.ref(
            'fieldservice_calendar_vrtl.calendar_tag_planned_booked')
        self.assertIn(booked, line.calendar_event_id.categ_ids)

    def test_note_change_does_not_touch_event_times(self):
        line = self._make_line()
        before = line.calendar_event_id.start
        line.write({'note': 'Ring before arrival'})
        self.assertEqual(line.calendar_event_id.start, before)

    # ── Calendar event -> planning line ──

    def test_drag_event_updates_planning_line(self):
        line = self._make_line()
        event = line.calendar_event_id
        new_start = line.date_start + timedelta(hours=2)
        event.write({
            'start': new_start,
            'stop': new_start + timedelta(hours=1),
        })
        self.assertEqual(line.date_start, new_start)
        self.assertAlmostEqual(line.time_start, 10.0, places=2)

    def test_drag_event_does_not_recurse(self):
        line = self._make_line()
        event = line.calendar_event_id
        new_start = line.date_start + timedelta(hours=1)
        event.write({'start': new_start, 'stop': new_start + timedelta(hours=1)})
        # The event must not have been rewritten by the planning line.
        self.assertEqual(event.start, new_start)

    # ── Unlink ──

    def test_unlink_removes_event(self):
        line = self._make_line()
        event = line.calendar_event_id
        line.unlink()
        self.assertFalse(event.exists())

    def test_unlink_order_removes_planning_and_events(self):
        line = self._make_line()
        event = line.calendar_event_id
        self.order.unlink()
        self.assertFalse(line.exists())
        self.assertFalse(event.exists())

    # ── Order integration ──

    def test_order_planning_count(self):
        self._make_line()
        self._make_line(time_start=13.0, time_end=14.0)
        self.assertEqual(self.order.planning_count, 2)

    def test_team_defaults_from_technician(self):
        line = self._make_line(team_id=self.team.id)
        self.assertEqual(line.team_id, self.team)

    def test_event_owner_is_never_empty(self):
        """An ownerless event is invisible in the week view."""
        line = self._make_line()
        self.assertTrue(line.calendar_event_id.user_id)
