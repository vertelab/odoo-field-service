from odoo import api, fields, models
import pytz


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    elevata_color = fields.Integer(
        string="Elevata Color Index",
        compute='_compute_elevata_color',
        store=True,
        default=0,
    )
    elevata_fsm_order_id = fields.Many2one(
        'fieldservice.order',
        string="Work Order",
        ondelete='set null',
        copy=False,
        index=True,
    )

    @api.depends('categ_ids', 'categ_ids.name')
    def _compute_user_can_edit(self):
        super()._compute_user_can_edit()
        locked_tag = self.env.ref(
            'elevata_base.calendar_tag_locked_timesheet',
            raise_if_not_found=False,
        )
        if locked_tag:
            for event in self:
                if locked_tag in event.categ_ids:
                    event.user_can_edit = False

    @api.depends('categ_ids', 'categ_ids.name')
    def _compute_elevata_color(self):
        for event in self:
            names = set(event.categ_ids.mapped('name'))
            if 'Planning Booked' in names:
                event.elevata_color = 3   # Red
            elif 'Planning Not Booked' in names:
                event.elevata_color = 2   # Green
            elif 'Timesheet' in names:
                event.elevata_color = 1   # Grey + border
            elif 'Locked Timesheet' in names:
                event.elevata_color = 8   # Light grey + border
            else:
                event.elevata_color = 0

    @api.model
    def get_elevata_color_config(self):
        get = self.env['ir.config_parameter'].sudo().get_param
        return {
            '2': {
                'bg': get('elevata_timesheet.color_planned_bg', '#27ae60'),
                'border': get('elevata_timesheet.color_planned_border', '#1e8449'),
                'text': get('elevata_timesheet.color_planned_text', '#ffffff'),
                'allBorder': False,
            },
            '3': {
                'bg': get('elevata_timesheet.color_booked_bg', '#e74c3c'),
                'border': get('elevata_timesheet.color_booked_border', '#a93226'),
                'text': get('elevata_timesheet.color_booked_text', '#ffffff'),
                'allBorder': False,
            },
            '1': {
                'bg': get('elevata_timesheet.color_timesheet_bg', '#95a5a6'),
                'border': get('elevata_timesheet.color_timesheet_border', '#717d7e'),
                'text': get('elevata_timesheet.color_timesheet_text', '#ffffff'),
                'allBorder': True,
            },
            '8': {
                'bg': get('elevata_timesheet.color_timesheet_locked_bg', '#bdc3c7'),
                'border': get('elevata_timesheet.color_timesheet_locked_border', '#95a5a6'),
                'text': get('elevata_timesheet.color_timesheet_locked_text', '#333333'),
                'allBorder': True,
            },
        }

    def _round_to_15min(self, float_time):
        return round(float_time * 4) / 4

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('no_calendar_sync_back'):
            return res
        if 'start' not in vals and 'stop' not in vals:
            return res
        for event in self:
            # Sync back to planning lines
            planning_lines = self.env['elevata.fsm.planning'].search([
                ('calendar_event_id', '=', event.id),
            ])
            if planning_lines:
                planning_vals = {}
                user_tz = pytz.timezone(self.env.user.tz or 'UTC')
                if event.start:
                    local_start = pytz.UTC.localize(event.start).astimezone(user_tz)
                    planning_vals['planning_date'] = local_start.date()
                    planning_vals['time_start'] = self._round_to_15min(
                        local_start.hour + local_start.minute / 60.0
                    )
                if event.stop:
                    local_stop = pytz.UTC.localize(event.stop).astimezone(user_tz)
                    planning_vals['time_end'] = self._round_to_15min(
                        local_stop.hour + local_stop.minute / 60.0
                    )
                if planning_vals:
                    planning_lines.with_context(
                        no_calendar_sync_back=True
                    ).write(planning_vals)

            # Sync back to timesheets
            timesheets = self.env['account.analytic.line'].search([
                ('calendar_event_id', '=', event.id),
            ], limit=1)
            if not timesheets:
                continue
            ts = timesheets[0]
            update_vals = {}
            user_tz = pytz.timezone(self.env.user.tz or 'UTC')
            if event.start:
                local_start = pytz.UTC.localize(event.start).astimezone(user_tz)
                update_vals['date'] = local_start.date()
                update_vals['time_start'] = self._round_to_15min(
                    local_start.hour + local_start.minute / 60.0
                )
            if event.stop:
                local_stop = pytz.UTC.localize(event.stop).astimezone(user_tz)
                update_vals['time_end'] = self._round_to_15min(
                    local_stop.hour + local_stop.minute / 60.0
                )
            if update_vals.get('time_start') and update_vals.get('time_end'):
                update_vals['unit_amount'] = update_vals['time_end'] - update_vals['time_start']
            if update_vals:
                ts.with_context(no_calendar_sync_back=True).write(update_vals)
        return res
