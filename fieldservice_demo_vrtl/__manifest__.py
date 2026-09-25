{
    'name': "Field service: Demo Vertel",
    'summary': "Demo data for field service orders.",
    'version': '18.0.1.0.0',
    'depends': ['fieldservice_vrtl','fieldservice_hr'],
    'author': "Vertel AB",
    "website": "https://vertel.se/apps/odoo-field-service/fieldservice_demo_vrtl",
    'category': 'Category',
    'license': 'AGPL-3',
    'description': '''
Demo Vertel
===========

    Demo data for field service orders.

    Features:

        - Guided Wizards: Step-by-step dialogs for data entry.
    ''',
    'data': [
        'wizard/create_demo_data_wizard.xml',
        'security/ir.model.access.csv'
    ],
}
