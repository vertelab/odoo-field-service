{
    'name': "Field service: Vertel",
    'summary': "Vertel extensions for field service orders.",
    'version': '18.0.1.0.0',
    'depends': ['mail','base','hr','project', 'product_brand'],
    'author': "Vertel AB",
    "website": "https://vertel.se/apps/odoo-field-service/fieldservice_vrtl",
    'category': 'Category',
    'license': 'AGPL-3',
    'description': '''
Vertel
======

    AI-based planning engine for Field Service.

Automatic scheduling based on SLA, workload and availability. Reduces manual
administration and improves resource utilisation.
    ''',
    'data': [
        'wizards/company_wizard_view.xml',
        'security/fieldservice_security.xml',
        'security/ir.model.access.csv',
        'views/fieldservice_order_views.xml',
        'views/fieldservice_order_line_views.xml',
        'views/fieldservice_order_type_view.xml',
        'views/fieldservice_stage_views.xml',
        'views/ir_config.xml',
        'views/product_views.xml',
        'data/fieldservice_project.xml',
        'data/fieldservice_stage_data.xml',
        'data/fieldservice_sequence_data.xml',
        'data/fieldservice_server_action.xml',
        #'demo/demo_employees.xml',
        #'demo/demo_work_orders.xml'
    ],

     "demo": [
        #  'demo/demo_employees.xml',
        #  'demo/demo_work_orders.xml'
     ],
}
