{
    'name': 'Field Service Stock Picking',
    'version': '1.0',
    'depends': ['fieldservice_vrtl', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/fieldservice_stock_picking_views.xml',


    ],
    'installable': True,
    'auto_install': False,
}
