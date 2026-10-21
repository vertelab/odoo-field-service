{
    'name': 'Elevata FSM Account',
    'version': '18.0.1.0.0',
    'category': 'Field Service',
    'summary': 'Invoicing of field service orders from timesheets and '
               'contractor costs',
    'author': 'Elevata',
    'license': 'AGPL-3',
    'depends': [
        'fieldservice_vrtl',
        'fieldservice_account_analytic',
        'elevata_fsm_flow',
        'hr_timesheet',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/fsm_order_cost_rules.xml',
        'data/time_products.xml',
        'views/fieldservice_order_views.xml',
        'views/account_move_views.xml',
        'views/hr_employee_views.xml',
        'views/account_analytic_line_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
