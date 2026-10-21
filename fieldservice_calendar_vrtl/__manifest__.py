{
    'name': 'Field Service - Planning (Vertel)',
    'version': '18.0.1.0.6',
    'category': 'Field Service',
    'summary': 'Plan field service orders on the calendar',
    'description': """
Field Service - Planning
========================

Planning is a core field service capability, so it lives here rather than
in a customer module. A work order is planned in three steps:

    fieldservice.order  ->  fieldservice.planning  ->  account.analytic.line

A planning line says when an order is scheduled and which technician does
it. It owns a calendar event, and the event is the same object the
technician drags around in the week view — moving it moves the plan.

Colour coding
-------------
Four calendar tags drive the colour of an event:

    Planning Booked        confirmed with the customer
    Planning Not Booked    technician assigned, not confirmed
    Timesheet              hours reported
    Locked Timesheet       hours reported and locked

The tags are defined here, not in a customer module, so the colour scheme
works on any field service installation.
""",
    'author': 'Vertel Sverige AB',
    'maintainer': 'Vertel Sverige AB',
    'website': 'https://www.vertel.se',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'license': 'AGPL-3',
    'depends': [
        'calendar',
        'fieldservice_vrtl',
        'fieldservice_maintenance',
    ],
    'data': [
        'data/calendar_event_type_data.xml',
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/hr_department_views.xml',
        'views/fieldservice_team_views.xml',
        'views/fieldservice_planning_views.xml',
        'views/fieldservice_planning_filter_views.xml',
        'views/fieldservice_order_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
