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

from datetime import date

from odoo.tests.common import TransactionCase


class TestTeamFilter(TransactionCase):
    """Per-user team checkboxes in the calendar sidebar."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Filter Customer'})
        cls.order = cls.env['fieldservice.order'].create({
            'name': 'FILTER-001',
            'partner_id': cls.partner.id,
        })
        cls.tech = cls.env['hr.employee'].create({'name': 'Filter Tech'})
        cls.team_a = cls.env['fieldservice.team'].create({
            'name': 'Team A',
            'member_ids': [(6, 0, cls.tech.ids)],
        })
        cls.team_b = cls.env['fieldservice.team'].create({'name': 'Team B'})
        cls.Filter = cls.env['calendar.filters.team']
        cls.Planning = cls.env['fieldservice.planning']

    def _line(self, team):
        return self.Planning.create({
            'fsm_order_id': self.order.id,
            'requested_employee_ids': self.tech.id,
            'team_id': team.id,
            'planning_date': date(2026, 5, 4),
            'time_start': 8.0,
            'time_end': 9.0,
        })

    def test_team_is_checked_by_default(self):
        """A team with no stored row must not vanish from the calendar."""
        line = self._line(self.team_a)
        self.assertTrue(line.team_checked)

    def test_unchecking_team_hides_it(self):
        line = self._line(self.team_a)
        self.Filter.create({
            'team_id': self.team_a.id,
            'team_checked': False,
        })
        self.assertFalse(self.Planning.browse(line.id).team_checked)

    def test_filter_is_per_user(self):
        other = self.env['res.users'].create({
            'name': 'Other Planner',
            'login': 'other_planner_filter_test',
            'email': 'other.planner@example.com',
            'groups_id': [(6, 0, [
                self.env.ref('fieldservice_vrtl.fieldservice_group_user').id,
            ])],
        })
        # Group membership is resolved lazily; flush so the new user can
        # read calendar.filters.team inside this same transaction.
        self.env.flush_all()
        self.Filter.create({
            'team_id': self.team_a.id,
            'team_checked': False,
        })
        line = self._line(self.team_a)
        self.assertFalse(self.Planning.browse(line.id).team_checked)
        self.assertTrue(
            self.Planning.with_user(other).browse(line.id).team_checked)

    def test_one_row_per_user_and_team(self):
        """The unique constraint is what keeps the checkbox state sane.

        Asserted against the constraint definition rather than by trying a
        duplicate insert: a failed insert aborts the test transaction and
        takes the remaining tests down with it.
        """
        names = [c[0] for c in self.Filter._sql_constraints]
        self.assertIn('user_id_team_id_unique', names)

    def test_teams_are_independent(self):
        self.Filter.create({'team_id': self.team_a.id, 'team_checked': False})
        line_a = self._line(self.team_a)
        line_b = self._line(self.team_b)
        self.assertFalse(self.Planning.browse(line_a.id).team_checked)
        self.assertTrue(self.Planning.browse(line_b.id).team_checked)

    def test_unlink_from_team_id_clears_rows(self):
        self.Filter.create({'team_id': self.team_a.id})
        self.Filter.unlink_from_team_id(self.team_a.id)
        self.assertFalse(self.Filter.search([('team_id', '=', self.team_a.id)]))

    def test_calendar_view_declares_team_filter(self):
        """The merged arch must carry the attributes the web client reads.

        Read through get_views, not view.arch: the latter is the base view
        only, without the inheriting view applied.
        """
        view = self.env.ref(
            'fieldservice_calendar_vrtl.fieldservice_planning_view_calendar')
        arch = self.env['fieldservice.planning'].get_views(
            [(view.id, 'calendar')])['views']['calendar']['arch']
        self.assertIn('write_model="calendar.filters.team"', arch)
        self.assertIn('filter_field="team_checked"', arch)
        self.assertIn('filters="1"', arch)
