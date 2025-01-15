{
    'name': "Fieldservice Vertel",
    'version': '1.0',
    'depends': ['mail','base','hr'],
    'author': "Vertel AB",
    'category': 'Category',
    'description': """
    Fieldservice
    """,
    'data': [
        'security/fieldservice_security.xml',
        'security/ir.model.access.csv',
        'views/fieldservice_order_views.xml',
        'data/fieldservice_stage_data.xml',
    ],
}
