# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestElevataTimesheet(TransactionCase):
    """Regression tests for the Elevata timesheet extension.

    The port had to reconcile three modules that all touch the same hours:
    hr_timesheet_begin_end (time_start/time_stop + constraint),
    project_timesheet_time_control (date_time -> unit_amount) and Elevata's
    own time_start/time_end pair.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Testkund Tidrapport AB',
            'is_company': True,
        })
        cls.equipment = cls.env['maintenance.equipment'].create({
            'name': 'TESTHISS-TS',
            'partner_id': cls.partner.id,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Tekniker TS',
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Testprojekt Tidrapport',
            'allow_timesheets': True,
        })

    def _line_vals(self, **overrides):
        vals = {
            'name': 'Testrad',
            'date': '2026-10-21',
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'time_start': 8.0,
            'time_stop': 10.0,
        }
        vals.update(overrides)
        return vals

    def test_unit_amount_from_hours(self):
        """unit_amount must equal time_stop - time_start, also with a project.

        hr_timesheet_begin_end validates this. Before the fix, the project
        path recomputed unit_amount from date_time and doubled it.
        """
        line = self.env['account.analytic.line'].create(self._line_vals())
        self.assertAlmostEqual(line.unit_amount, 2.0)

    def test_unit_amount_without_project(self):
        line = self.env['account.analytic.line'].create(
            self._line_vals(project_id=False))
        self.assertAlmostEqual(line.unit_amount, 2.0)

    def test_time_end_mirrors_time_stop(self):
        """Elevata's time_end must follow hr_timesheet_begin_end's time_stop."""
        line = self.env['account.analytic.line'].create(self._line_vals())
        self.assertAlmostEqual(line.time_end, 10.0)
        self.assertAlmostEqual(line.time_stop, 10.0)

    def test_datetime_fields_computed(self):
        line = self.env['account.analytic.line'].create(self._line_vals())
        self.assertTrue(line.datetime_start)
        self.assertTrue(line.datetime_end)
        delta = line.datetime_end - line.datetime_start
        self.assertAlmostEqual(delta.total_seconds() / 3600.0, 2.0)

    def test_zero_hours_allowed(self):
        """A line without hours must not trip the start/stop constraint.

        The original constraint used truthiness (0.0 is falsy), so a
        half-filled record was validated against time_end = 0.
        """
        line = self.env['account.analytic.line'].create({
            'name': 'Utan tider',
            'date': '2026-10-21',
            'employee_id': self.employee.id,
            'project_id': self.project.id,
        })
        self.assertAlmostEqual(line.unit_amount, 0.0)

    def test_start_after_stop_rejected(self):
        with self.assertRaises(ValidationError):
            self.env['account.analytic.line'].create(
                self._line_vals(time_start=12.0, time_stop=9.0))

    def test_timesheet_on_order(self):
        """A timesheet linked to a field service order lands in timesheet_ids."""
        order = self.env['fieldservice.order'].create({
            'name': 'TEST-ORDER-TS',
            'equipment_id': self.equipment.id,
        })
        line = self.env['account.analytic.line'].create({
            'name': 'Orderrad',
            'date': '2026-10-21',
            'employee_id': self.employee.id,
            'task_id': order.task_id.id,
            'time_start': 8.0,
            'time_stop': 10.0,
        })
        self.assertAlmostEqual(line.unit_amount, 2.0)
        self.assertIn(line, order.timesheet_ids)
