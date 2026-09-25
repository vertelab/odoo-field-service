{
    'name': 'Field Service: Sale',
    'version': '18.0.1.0.0',
    'summary': 'Integrate Field Service with Sales.',
    'description': '''
Sale
====

    Integrate Field Service with Sales.

    Features:

        - UI Integration: Extends 1 view(s) in the Odoo interface.
        - Extends Odoo: Builds on fieldservice.order, product.template, sale.order, sale.order.line.
    ''',
    'category': 'Services/Field Service',

    'depends': ['fieldservice_vrtl', 'sale'],
    'data': [
        'views/fieldservice_sale_order_views.xml',
        #'views/fieldservice_sale_views.xml',
        
    ],
    'author': ' Company',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_sale_vrtl',
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
}
