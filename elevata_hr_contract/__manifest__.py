{
    'name': 'Elevata Swedish Employment Contracts',
    'version': '18.0.1.0.1',
    'category': 'Human Resources',
    'summary': 'Extends hr.contract with Swedish employment fields',
    'description': """
        Adds Swedish fields to employment contracts:
        - Employment form (permanent, fixed term, probation, temporary)
        - Collective agreement
        - Notice period (employee/employer)
        - Vacation days
        - Employment percentage
    """,
    'author': 'Elevata Hiss AB',
    'website': 'https://www.elevata.se',
    'depends': [
        'hr_contract',
        'hr_holidays',
    ],
    'data': [
        'data/sequence_data.xml',
        'data/leave_type_data.xml',
        'data/contract_type_data.xml',
        'reports/contract_report.xml',
        'data/email_template.xml',
        'data/cron_data.xml',
        'views/hr_contract_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
