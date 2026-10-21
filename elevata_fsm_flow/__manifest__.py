# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# Version ledger
#   18.0.1.0.0  2026-10-21  Ported from Odoo 17 / OCA fieldservice. fsm.location
#                           split into maintenance.equipment (the elevator) and
#                           property.property (the address); order type reached
#                           through product_tmpl_id.product_type.
{
    'name': 'Elevata FSM Flow',
    'version': '18.0.1.0.1',
    'category': 'Field Service',
    'summary': 'Core FSM module: stages, elevator data, order workflow, views',
    'author': 'Vertel Sverige AB',
    'maintainer': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-field-service/elevata_fsm_flow',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'license': 'AGPL-3',
    'images': ['static/description/banner.png'],
    'depends': [
        'fieldservice_vrtl',
        'fieldservice_maintenance',
        'fieldservice_maintenance_vrtl',
        'fieldservice_project_vrtl',
        'fieldservice_recurring_vrtl',
        'fieldservice_order_type_color',
        'maintenance_elevator',
        'property_maintanance',
        'hr_timesheet',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        # Data
        'data/fsm_stage_data.xml',
        'data/fsm_dashboard_data.xml',
        'data/fsm_technician_menu.xml',
        # Views — the elevator (maintenance.equipment)
        'views/fsm_location_form_views.xml',
        'views/fsm_location_tree_views.xml',
        'views/fsm_location_menus.xml',
        # Views — orders
        'views/fsm_order_form_views.xml',
        'views/fsm_order_tree_views.xml',
        'views/fsm_order_kanban_views.xml',
        # Wizard
        'wizard/elevator_shutdown_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'elevata_fsm_flow/static/src/js/colored_priority_field.js',
            'elevata_fsm_flow/static/src/xml/colored_priority_field.xml',
            'elevata_fsm_flow/static/src/scss/colored_priority_field.scss',
            'elevata_fsm_flow/static/src/js/fsm_dashboard.js',
            'elevata_fsm_flow/static/src/xml/fsm_dashboard.xml',
            'elevata_fsm_flow/static/src/scss/fsm_dashboard.scss',
            'elevata_fsm_flow/static/src/js/fsm_tech_dashboard.js',
            'elevata_fsm_flow/static/src/xml/fsm_tech_dashboard.xml',
            'elevata_fsm_flow/static/src/js/technician_filter_menu.js',
            'elevata_fsm_flow/static/src/xml/technician_filter_menu.xml',
        ],
    },
    'installable': True,
    'application': True,
}
