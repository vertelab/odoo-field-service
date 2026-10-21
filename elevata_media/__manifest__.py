{
    'name': 'Elevata Media',
    'version': '18.0.1.0.0',
    'category': 'Field Service',
    'summary': 'Shared image archive for elevators and work orders',
    'author': 'Elevata Hiss AB',
    'website': 'https://www.elevata.se',
    'depends': [
        'elevata_fsm_flow',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/media_image_views.xml',
        'views/fieldservice_order_views.xml',
        'views/maintenance_equipment_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'elevata_media/static/src/scss/media.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
