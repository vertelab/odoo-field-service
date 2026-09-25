{
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_material_vrtl',
    'name': 'Field Service: Stock Picking',
    'summary': "Adds material lines to field service orders.",
    'description': '''
Stock Picking
=============

    Adds material lines to field service orders.

    Features:

        - UI Integration: Extends 1 view(s) in the Odoo interface.
        - Extends Odoo: Builds on fieldservice.order.line, fieldservice.order.line.material, fieldservice.order.line.material.request, product_id.
    ''',
    'version': '18.0.1.0.0',
    'depends': ['fieldservice_vrtl', 'stock'],
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/fieldservice_stock_picking_views.xml',


    ],
    'installable': True,
    'auto_install': False,
}
