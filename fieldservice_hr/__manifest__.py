{
    'name': "Field service: HR Vertel",
    'summary': "Links field service orders to employees.",
    'version': '18.0.1.0.0',
    'depends': ['fieldservice_vrtl','hr_timesheet','hr'],
    'author': "Vertel AB",
    "website": "https://vertel.se/apps/odoo-field-service/fieldservice_hr",
    'category': 'Category',
    'license': 'AGPL-3',
    'description': '''
HR Vertel
=========

    Links field service orders to employees.

    Features:

        - UI Integration: Extends 4 view(s) in the Odoo interface.
        - Extends Odoo: Builds on account.analytic.line, fieldservice.order, fieldservice.order.line, fieldservice.order.line.employee.
    ''',
    'data': [
        'security/ir.model.access.csv',
        'security/fieldservice_hr_security.xml',
        'views/fieldservice_order_line_employee_views.xml',
        'views/fieldservice_order_view.xml',
        'views/fieldservice_order_line_views.xml',
        'views/resource_view.xml'

    ],
}
