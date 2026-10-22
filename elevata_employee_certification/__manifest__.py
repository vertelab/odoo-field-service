{
    'name': 'Elevata Employee Certification',
    'version': '18.0.1.0.1',
    'category': 'Elevata/HR',
    'summary': 'Certification management with expiry dates and reminders for employees',
    'author': 'Elevata',
    'website': 'https://www.elevata.se',
    'depends': [
        'hr',
        'hr_skills',
        'elevata_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/skill_data.xml',
        'data/cron_data.xml',
        'views/employee_views.xml',
        'views/certification_overview_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
