{
    'name': 'SLA Management',
    'version': '18.0.1.0.0',
    'summary': 'Manage SLA agreements and track service level compliance.',
    'description': '''
SLA Management
==============

    Manage SLA agreements and track service level compliance.

    Features:

        - Automation: Scheduled jobs: Check SLA Breaches.
        - UI Integration: Extends 2 view(s) in the Odoo interface.
        - Extends Odoo: Builds on fieldservice.order, fieldservice.order.sla, fieldservice.sla, fieldservice.stage.
    ''',
    'category': 'Services',
    'author': 'Your Name or Company',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_sla',
    'license': 'AGPL-3',
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
