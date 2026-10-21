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
##############################################################################

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCalendarOwner(TransactionCase):
    """The four levels: company, department, team, individual."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.user_company = cls.env['res.users'].create({
            'name': 'Company Owner',
            'login': 'owner_company_test',
            'email': 'company.owner@example.com',
        })
        cls.user_dept = cls.env['res.users'].create({
            'name': 'Department Owner',
            'login': 'owner_dept_test',
            'email': 'dept.owner@example.com',
        })
        cls.user_team = cls.env['res.users'].create({
            'name': 'Team Owner',
            'login': 'owner_team_test',
            'email': 'team.owner@example.com',
        })
        cls.user_tech = cls.env['res.users'].create({
            'name': 'Technician User',
            'login': 'owner_tech_test',
            'email': 'tech.user@example.com',
        })
        cls.manager = cls.env['hr.employee'].create({
            'name': 'Department Manager',
            'user_id': cls.user_dept.id,
        })
        cls.department = cls.env['hr.department'].create({
            'name': 'Service Test Dept',
            'manager_id': cls.manager.id,
        })
        cls.team = cls.env['fieldservice.team'].create({
            'name': 'Owner Chain Team',
            'department_id': cls.department.id,
        })

    def _make_planning(self, team=None):
        order = self.env['fieldservice.order'].create({
            'name': 'OWNER-CHAIN-1',
            'partner_id': self.env['res.partner'].create(
                {'name': 'Owner Chain Customer'}).id,
        })
        return self.env['fieldservice.planning'].create({
            'fsm_order_id': order.id,
            'team_id': (team or self.team).id,
            'planning_date': '2026-07-01',
            'time_start': 8.0,
            'time_end': 9.0,
        })

    # --- level by level ------------------------------------------------

    def test_team_owner_wins(self):
        """The team's own owner beats department and company."""
        self.team.calendar_user_id = self.user_team
        line = self._make_planning()
        self.assertEqual(line._get_calendar_user(), self.user_team)

    def test_department_owner_used_when_team_has_none(self):
        """No team owner falls through to the department."""
        line = self._make_planning()
        self.assertEqual(line._get_calendar_user(), self.user_dept)

    def test_company_owner_used_when_department_has_none(self):
        """No department owner falls through to the company."""
        self.department.manager_id = False
        self.company.fsm_calendar_user_id = self.user_company
        line = self._make_planning()
        self.assertEqual(line._get_calendar_user(), self.user_company)

    def test_individual_used_when_nothing_above_resolves(self):
        """Nothing configured: the technician's own user is the owner."""
        self.department.manager_id = False
        self.company.fsm_calendar_user_id = False
        employee = self.env['hr.employee'].create({
            'name': 'Owner Chain Tech',
            'user_id': self.user_tech.id,
        })
        line = self._make_planning()
        line.requested_employee_ids = employee.id
        self.assertEqual(line._get_calendar_user(), self.user_tech)

    def test_owner_is_never_empty(self):
        """Last resort is the current user — an ownerless event is invisible."""
        self.department.manager_id = False
        self.company.fsm_calendar_user_id = False
        line = self._make_planning()
        self.assertTrue(line._get_calendar_user())

    def test_sub_department_inherits_parent_owner(self):
        """A sub-department without an owner uses its parent's."""
        child = self.env['hr.department'].create({
            'name': 'Service Test Sub Dept',
            'parent_id': self.department.id,
        })
        self.assertEqual(child._get_fsm_calendar_user(), self.user_dept)

    # --- participants --------------------------------------------------

    def test_technician_without_user_becomes_participant(self):
        """A technician without an account still appears on the event.

        This is the real gap: 11 of 12 technicians have no user, so the
        old tech.user_id.partner_id lookup dropped them silently.
        """
        employee = self.env['hr.employee'].create({'name': 'No Account Tech'})
        self.assertFalse(employee.user_id)
        line = self._make_planning()
        line.requested_employee_ids = employee.id
        partners = line._get_participant_partners()
        self.assertIn(employee.name, partners.mapped('name'))

    def test_technician_partner_is_reused(self):
        """A second call must not create a second contact."""
        employee = self.env['hr.employee'].create({'name': 'Reuse Tech'})
        first = employee._get_calendar_partner()
        second = employee._get_calendar_partner()
        self.assertEqual(first, second)

    def test_participants_include_customer(self):
        """The customer is on the event too, not just the technicians."""
        line = self._make_planning()
        partners = line._get_participant_partners()
        self.assertIn(line.fsm_order_id.partner_id, partners)

    def test_event_carries_all_participants(self):
        """The prepared values list every requested technician."""
        employee = self.env['hr.employee'].create({'name': 'Event Tech'})
        line = self._make_planning()
        line.requested_employee_ids = employee.id
        vals = line._prepare_calendar_event_vals()
        partner_ids = vals['partner_ids'][0][2]
        self.assertIn(line.fsm_order_id.partner_id.id, partner_ids)
        self.assertIn(employee._get_calendar_partner().id, partner_ids)

    # --- technician is a real user -------------------------------------

    def test_fieldservice_user_implies_internal_user(self):
        """Field Service User must imply base.group_user.

        Every calendar.event ACL row is keyed on base.group_user or
        narrower, so without this a technician holding only the Field
        Service role gets AccessError instead of their week view.
        """
        group = self.env.ref('fieldservice_vrtl.fieldservice_group_user')
        self.assertIn(self.env.ref('base.group_user'), group.implied_ids)

    def test_technician_can_read_calendar(self):
        """A technician with only the Field Service role can read events."""
        group = self.env.ref('fieldservice_vrtl.fieldservice_group_user')
        technician = self.env['res.users'].create({
            'name': 'Real Technician',
            'login': 'real_technician_test',
            'email': 'real.tech@example.com',
            'groups_id': [(6, 0, [group.id])],
        })
        self.env.flush_all()
        event = self.env['calendar.event'].create({
            'name': 'Technician Visible',
            'start': '2026-07-01 08:00:00',
            'stop': '2026-07-01 09:00:00',
            'user_id': technician.id,
        })
        self.assertTrue(
            self.env['calendar.event'].with_user(technician).search_count(
                [('id', '=', event.id)]),
            'A technician must be able to see their own calendar event',
        )
