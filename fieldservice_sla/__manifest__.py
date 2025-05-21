{
    'name': 'SLA Management',
    'version': '1.0',
    'summary': 'Manage SLA agreements and track service level compliance',
    'category': 'Services',
    'author': 'Your Name or Company',
    'license': 'LGPL-3',
    'depends': ['base', 'fieldservice_vrtl','hr'],  
    'data': [
        'data/cron_jobs.xml',
        'views/fieldservice_inherit_views.xml',
        'security/ir.model.access.csv',
        'views/fieldservice_sla_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
