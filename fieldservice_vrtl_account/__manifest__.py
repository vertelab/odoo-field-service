{
    'name': "Field service: HR Vertel",
    'summary': "Links field service orders to accounting.",
    'version': '18.0.1.0.0',
    'depends': ['fieldservice_vrtl','hr_timesheet','hr'],
    'author': "Vertel AB",
    "website": "https://vertel.se/apps/odoo-field-service/fieldservice_vrtl_account",
    'category': 'Category',
    'license': 'AGPL-3',
    'description': '''
HR Vertel
=========

    Links field service orders to accounting.

    Features:

        - UI Integration: Extends 4 view(s) in the Odoo interface.
        - Extends Odoo: Builds on account.move, fieldservice.invoice.line, fieldservice.order.
    ''',
    'data': [
        'security/ir.model.access.csv',
        'views/fieldservice_order_view.xml',
    ],
}
