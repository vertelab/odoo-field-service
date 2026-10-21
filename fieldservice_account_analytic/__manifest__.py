{
    'name': 'Field Service Account Analytic',
    'version': '18.0.1.0.1',
    'category': 'Field Service',
    'summary': 'Analytic accounting for field service orders and timesheets',
    'author': 'Vertel Sverige AB',
    'website': 'https://www.vertel.se',
    'license': 'AGPL-3',
    'depends': [
        'fieldservice_vrtl',
        'hr_timesheet',
        'account',
        'property_mgmt',
        # The inherited order form calls action_assign, action_schedule and
        # action_start. Those methods live in elevata_fsm_flow, so without
        # this dependency the view fails validation with
        # "action_assign is not a valid action on fieldservice.order" as
        # soon as fieldservice_vrtl is upgraded and the view is revalidated.
        'elevata_fsm_flow',
    ],
    'data': [
        'views/fieldservice_order_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/account_analytic_line_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
