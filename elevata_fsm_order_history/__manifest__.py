{
    'name': 'Elevata FSM Order History',
    'version': '18.0.1.0.1',
    'category': 'Field Service',
    'summary': 'Order history views for FSM orders and locations',
    'author': 'Vertel Sverige AB',
    'maintainer': 'Vertel Sverige AB',
    'website': 'https://vertel.se',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'license': 'AGPL-3',
    'images': ['static/description/banner.png'],
    'depends': [
        'fieldservice_vrtl',
        'elevata_fsm_flow',
        'fieldservice_order_type_color',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fsm_order_history_views.xml',
    ],
    'installable': True,
    'application': False,
}
