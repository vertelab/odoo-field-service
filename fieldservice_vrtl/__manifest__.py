{
    'name': "Field service: Vertel",
    'version': '1.0',
    'depends': ['mail','base','hr','project', 'product_brand'],
    'author': "Vertel AB",
    'category': 'Category',
    'license': 'LGPL-3',
    'description': """AI-baserad planeringsmotor för Field Service. Automatisk schemaläggning baserat på SLA, arbetsbörda och tillgänglighet. 
    Minskar manuell administration och förbättrar resursutnyttjande."
    Fieldservice
    """,
    'data': [
        'wizards/company_wizard_view.xml',
        'security/fieldservice_security.xml',
        'security/ir.model.access.csv',
        'views/fieldservice_order_views.xml',
        'views/fieldservice_order_line_views.xml',
        'views/fieldservice_order_type_view.xml',
        'views/fieldservice_stage_views.xml',
        'views/ir_config.xml',
        'views/product_views.xml'
        'data/fieldservice_project.xml',
        'data/fieldservice_stage_data.xml',
        'data/fieldservice_sequence_data.xml'
        'data/fieldservice_server_action.xml'
        #'demo/demo_employees.xml',
        #'demo/demo_work_orders.xml'
    ],

     "demo": [
        #  'demo/demo_employees.xml',
        #  'demo/demo_work_orders.xml'
     ],
}

