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
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
