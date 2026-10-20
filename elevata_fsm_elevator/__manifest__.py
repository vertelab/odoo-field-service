{
    'name': 'Elevata FSM Elevator',
    'version': '18.0.1.0.0',
    'category': 'Field Service',
    'summary': 'Unique elevator number sequence (Hxxxxx) on maintenance equipment',
    'author': 'Elevata',
    'website': 'https://www.elevata.se',
    'depends': [
        'maintenance',
    ],
    'data': [
        'data/elevator_number_sequence.xml',
        'views/maintenance_equipment_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
