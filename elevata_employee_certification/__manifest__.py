{
    'name': 'Elevata Employee Certification',
    'version': '18.0.1.0.2',
    'category': 'Elevata/HR',
    'summary': 'Certification management with expiry dates and reminders for employees',
    'author': 'Elevata',
    'website': 'https://www.elevata.se',
    'depends': [
        'hr',
        'hr_skills',
        'elevata_base',
        # The certifications themselves come from the odoo-hr bridges.
        # Seeding them here as well gave the same certification twice under
        # two skill types, and the CV showed both.
        'hr_skills_certificate',
        'hr_certificate_hiss',
        'hr_certificate_esa',
        'hr_certificate_arbetsmiljo',
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
