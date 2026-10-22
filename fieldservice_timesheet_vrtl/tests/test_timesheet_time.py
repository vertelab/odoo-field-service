from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTimesheetTime(TransactionCase):
    """Time mechanics on account.analytic.line.

    The 15 minute grid is the contract between a plan and a reported hour, so
    these tests pin the boundary behaviour rather than the happy path only.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'FSM Timesheet Test'})
        cls.Line = cls.env['account.analytic.line']
        # hr_timesheet refuses a timesheet without an employee on the line.
        cls.employee = cls.env['hr.employee'].create({
            'name': 'FSM Test Technician',
            'user_id': cls.env.user.id,
        })

    def _line(self, **vals):
        base = {
            'name': 'Work',
            'project_id': self.project.id,
            'date': '2026-10-22',
            'employee_id': self.employee.id,
        }
        base.update(vals)
        # hr_timesheet_begin_end requires unit_amount to equal the difference
        # between time_start and time_stop. Derive it instead of hardcoding.
        if 'unit_amount' not in base:
            start = base.get('time_start') or 0.0
            stop = base.get('time_stop') or 0.0
            base['unit_amount'] = round(stop - start, 2) if stop > start else 1.0
        return self.Line.create(base)

    # ── Valid values ──

    def test_quarter_hours_accepted(self):
        line = self._line(time_start=8.0, time_stop=9.25)
        self.assertEqual(line.time_start, 8.0)
        self.assertEqual(line.time_stop, 9.25)

    def test_half_filled_record_not_rejected_by_our_validation(self):
        """Our constraint must not fire on a half-filled record.

        hr_timesheet_begin_end owns time_stop and rejects a missing end hour
        on its own, so exercise our constraint directly rather than through
        create().
        """
        line = self.Line.new({'time_start': 8.5, 'time_stop': 0.0})
        line._check_time_validity()
        line._check_interval()

    def test_midnight_boundaries_accepted(self):
        line = self._line(time_start=0.0, time_stop=23.75)
        self.assertEqual(line.time_stop, 23.75)

    # ── Rejected values ──

    def test_start_after_end_rejected(self):
        with self.assertRaises(ValidationError):
            self._line(time_start=10.0, time_stop=9.0)

    def test_equal_start_and_end_rejected(self):
        with self.assertRaises(ValidationError):
            self._line(time_start=9.0, time_stop=9.0)

    def test_start_outside_day_rejected(self):
        with self.assertRaises(ValidationError):
            self._line(time_start=24.5, time_stop=25.0)

    def test_off_grid_start_rejected(self):
        with self.assertRaises(ValidationError):
            self._line(time_start=8.1, time_stop=9.0)

    def test_off_grid_end_rejected(self):
        with self.assertRaises(ValidationError):
            self._line(time_start=8.0, time_stop=9.4)

    # ── Datetime round trip ──

    def test_datetime_start_derived_from_float(self):
        line = self._line(time_start=8.0, time_stop=9.0)
        self.assertTrue(line.datetime_start)
        self.assertTrue(line.datetime_end)
        self.assertLess(line.datetime_start, line.datetime_end)

    def test_datetime_inverse_writes_back_float(self):
        """A datetime write must land as a wall-clock float.

        The user's timezone shifts the hour, so assert the relationship
        between the two values rather than an absolute number.
        """
        line = self._line(time_start=8.0, time_stop=9.0)
        line.write({
            'datetime_start': '2026-10-22 12:00:00',
            'datetime_end': '2026-10-22 13:00:00',
        })
        self.assertLess(line.time_start, line.time_stop)
        self.assertAlmostEqual(line.time_stop - line.time_start, 1.0, places=2)

    # ── Hour derivation ──

    def test_unit_amount_from_onchange(self):
        line = self.Line.new({
            'project_id': self.project.id,
            'date': '2026-10-22',
            'employee_id': self.employee.id,
            'time_start': 8.0,
            'time_end': 10.5,
        })
        line._onchange_times()
        self.assertEqual(line.unit_amount, 2.5)
