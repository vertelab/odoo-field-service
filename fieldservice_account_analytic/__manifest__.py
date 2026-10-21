{
    'name': 'Field Service Account Analytic',
    'version': '18.0.1.0.0',
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
