{
    'name': 'Field Service: PWA Support',
    'version': '1.0',
    'category': 'Technical',
    'depends': ['base', 'web'],
    'data': [
        'views/pwa_manifest.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/field_service_pwa_support/static/src/js/pwa.js',
        ],
        'web.assets_common': [
            ('include', 'web.assets_backend'),
            '/field_service_pwa_support/views/pwa_manifest.xml',
        ],
    },

    'application': False,
    'installable': True,
    'auto_install': False,
    'pwa': True,
}
