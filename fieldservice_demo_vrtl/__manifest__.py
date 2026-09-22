{
    'name': "Field service: Demo Vertel",
    'version': '1.0',
    'depends': ['fieldservice_vrtl','fieldservice_hr'],
    'author': "Vertel AB",
    "website": "https://vertel.se/apps/odoo-field-service/fieldservice_demo_vrtl",
    'category': 'Category',
    'license': 'AGPL-3',
    'description': """
    Fieldservice
    """,
    'data': [
        'wizard/create_demo_data_wizard.xml',
        'security/ir.model.access.csv'
    ],
}
