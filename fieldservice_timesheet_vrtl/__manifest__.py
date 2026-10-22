{
    'name': 'Field Service - Timesheet (Vertel)',
    'version': '18.0.1.0.3',
    'category': 'Field Service',
    'summary': 'Start/end time and interval validation on timesheets',
    'description': """
Field Service - Timesheet
=========================

Reporting hours on a work order is a core field service capability, so the
time mechanics live here rather than in a customer module.

What this module owns
---------------------
* ``time_start`` / ``time_end`` on ``account.analytic.line`` — the hours a
  technician actually worked, as wall-clock floats.
* ``datetime_start`` / ``datetime_end`` — the same values as timezone-aware
  datetimes, computed and inverse so either representation can be written.
* Validation: start before end, both inside 0-24, and both on a 15 minute
  boundary. The 15 minute grid is what the planning calendar snaps to, so a
  timesheet that does not sit on it cannot be matched to a plan.
* ``unit_amount`` is derived from the difference when both ends are set.

What this module does NOT own
-----------------------------
Billing rates. A rate type (normal hours, overtime, weekend, on-call) and
its price come from the customer's agreement and belong in the customer
module that knows about agreements.

Dependency direction
--------------------
``elevata_*`` depends on ``fieldservice_*``, never the other way around.
""",
    'author': 'Vertel Sverige AB',
    'maintainer': 'Vertel Sverige AB',
    'website': 'https://www.vertel.se',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'license': 'AGPL-3',
    'depends': [
        'hr_timesheet',
        'hr_timesheet_begin_end',
        'fieldservice_vrtl',
        # calendar.event and calendar.event.type, used by the calendar sync
        'calendar',
    ],
    'data': [
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
