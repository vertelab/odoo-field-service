{
    'name': 'Elevata Timesheet',
    'version': '18.0.1.0.13',
    'category': 'Human Resources/Timesheets',
    'summary': 'Start/end time, rate types, contract prices, and calendar sync for timesheets',
    'author': 'Vertel Sverige AB',
    'maintainer': 'Vertel Sverige AB',
    'website': 'https://vertel.se',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'license': 'AGPL-3',
    'images': ['static/description/banner.png'],
    'depends': [
        'hr_timesheet',
        'hr_timesheet_calendar',
        # account_analytic_line.py reads record.time_stop in
        # _compute_datetime_fields, and the comment there says
        # hr_timesheet_begin_end owns time_start/time_stop. It was missing
        # from depends, so the field did not exist and the module crashed
        # at registry load:
        #   AttributeError: 'account.analytic.line' object has no attribute 'time_stop'
        'hr_timesheet_begin_end',
        'calendar',
        'fieldservice_vrtl',
        'elevata_base',
        'timepicker_field',
        'fieldservice_order_type_color',
        'elevata_fsm_flow',
        'elevata_fsm_account',
        # Planning lines and action_convert_to_timesheet live in the generic
        # fieldservice_calendar_vrtl. elevata_timesheet used to carry its own
        # elevata.fsm.planning copy; it was removed as a duplicate.
        'fieldservice_calendar_vrtl',
        'fieldservice_timesheet_vrtl',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/project_data.xml',
        'data/mail_template_data.xml',
        'data/calendar_color_data.xml',
        'views/timesheet_views.xml',
        'views/calendar_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'elevata_timesheet/static/src/xml/calendar_popover_patch.xml',
            'elevata_timesheet/static/src/js/calendar_planning_patch.js',
            'elevata_timesheet/static/src/scss/calendar_planning.scss',
        ],
    },
    'installable': True,
    'application': False,
}
