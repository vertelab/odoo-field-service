{
    'name': "Fieldservice HR Vertel",
    'version': '1.0',
    'depends': ['fieldservice_vrtl','hr_timesheet','hr'],
    'author': "Vertel AB",
    'category': 'Category',
    'license': 'LGPL-3',
    'description': """
    Fieldservice
    """,
    'data': [
        'views/fieldservice_timesheet_views.xml',
        'views/fieldservice_order_line_employee_views.xml',
        'security/ir.model.access.csv'
    ],
}