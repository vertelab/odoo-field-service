{
    'name': "Field service: Demo Vertel",
    'version': '18.0.1.0.0',
    'depends': ['fieldservice_vrtl','fieldservice_hr_vrtl'],
    'author': "Vertel Sverige AB",
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
