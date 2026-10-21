from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ── Calendar event colors ──

    calendar_color_planned_bg = fields.Char(
        string="Planned — Background",
        config_parameter='elevata_timesheet.color_planned_bg',
        default='#27ae60',
    )
    calendar_color_planned_border = fields.Char(
        string="Planned — Border",
        config_parameter='elevata_timesheet.color_planned_border',
        default='#1e8449',
    )
    calendar_color_planned_text = fields.Char(
        string="Planned — Text",
        config_parameter='elevata_timesheet.color_planned_text',
        default='#ffffff',
    )

    calendar_color_booked_bg = fields.Char(
        string="Planned Booked — Background",
        config_parameter='elevata_timesheet.color_booked_bg',
        default='#e74c3c',
    )
    calendar_color_booked_border = fields.Char(
        string="Planned Booked — Border",
        config_parameter='elevata_timesheet.color_booked_border',
        default='#a93226',
    )
    calendar_color_booked_text = fields.Char(
        string="Planned Booked — Text",
        config_parameter='elevata_timesheet.color_booked_text',
        default='#ffffff',
    )

    calendar_color_timesheet_bg = fields.Char(
        string="Timesheet — Background",
        config_parameter='elevata_timesheet.color_timesheet_bg',
        default='#95a5a6',
    )
    calendar_color_timesheet_border = fields.Char(
        string="Timesheet — Border",
        config_parameter='elevata_timesheet.color_timesheet_border',
        default='#717d7e',
    )
    calendar_color_timesheet_text = fields.Char(
        string="Timesheet — Text",
        config_parameter='elevata_timesheet.color_timesheet_text',
        default='#ffffff',
    )

    calendar_color_timesheet_locked_bg = fields.Char(
        string="Timesheet Locked — Background",
        config_parameter='elevata_timesheet.color_timesheet_locked_bg',
        default='#bdc3c7',
    )
    calendar_color_timesheet_locked_border = fields.Char(
        string="Timesheet Locked — Border",
        config_parameter='elevata_timesheet.color_timesheet_locked_border',
        default='#95a5a6',
    )
    calendar_color_timesheet_locked_text = fields.Char(
        string="Timesheet Locked — Text",
        config_parameter='elevata_timesheet.color_timesheet_locked_text',
        default='#333333',
    )
