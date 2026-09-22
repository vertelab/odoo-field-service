{
    'name': 'Field Service: Sale',
    'version': '1.0',
    'summary': 'Integrate Field Service with Sales',
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
