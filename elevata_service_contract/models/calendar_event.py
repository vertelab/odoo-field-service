from math import floor

from odoo import models


def _round_to_15min(dt):
    if not dt:
        return dt
    rounded_min = floor(dt.minute / 15) * 15
    return dt.replace(minute=rounded_min, second=0, microsecond=0)


class CalendarEventElevata(models.Model):
    _inherit = 'calendar.event'

    def write(self, vals):
        res = super().write(vals)
        if self._context.get('recurse_time_line'):
            return res
        if 'start' not in vals and 'stop' not in vals:
            return res
        for event in self:
            time_lines = self.env['elevata.fsm.time.line'].search(
                [('calendar_event_id', '=', event.id)]
            )
            if not time_lines:
                continue
            update = {}
            if 'start' in vals:
                update['datetime_from'] = _round_to_15min(event.start)
            if 'stop' in vals:
                update['datetime_to'] = _round_to_15min(event.stop)
            if update:
                time_lines.with_context(
                    recurse_time_line=True
                ).write(update)
        return res
