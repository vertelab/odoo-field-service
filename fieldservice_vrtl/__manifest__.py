{
    'name': "Fieldservice Vertel",
    'version': '1.0',
    'depends': ['mail','base','hr'],
    'author': "Vertel AB",
    'category': 'Category',
    'license': 'LGPL-3',
    'description': """
    Fieldservice
    """,
    'data': [
        'wizards/company_wizard_view.xml',
        'security/fieldservice_security.xml',
        'security/ir.model.access.csv',
        'views/fieldservice_order_views.xml',
        'views/fieldservice_order_line_views.xml',
        'data/fieldservice_stage_data.xml',
        #'demo/demo_employees.xml',
        #'demo/demo_work_orders.xml'
    ],

     "demo": [
         'demo/demo_employees.xml',
         'demo/demo_work_orders.xml'
     ],
}
