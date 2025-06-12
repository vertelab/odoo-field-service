{
    'name': "Field service: HR Vertel",
    'version': '1.0',
    'depends': ['fieldservice_vrtl','hr_timesheet','hr'],
    'author': "Vertel AB",
    'category': 'Category',
    'license': 'LGPL-3',
    'description': """
    Fieldservice
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/fieldservice_order_view.xml',
    ],
}
