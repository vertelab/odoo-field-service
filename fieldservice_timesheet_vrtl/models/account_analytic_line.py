from datetime import datetime, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# The planning calendar snaps to this grid, so a timesheet that does not sit
# on it cannot be matched to a plan. Kept as a class attribute so a customer
# module can widen it without copying the validation.
INTERVAL_MINUTES = 15


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    # hr_timesheet_begin_end owns time_start/time_stop and hard-validates
    # time_stop >= time_start. Elevata code and views use time_end, so make
    # it a writable alias of time_stop instead of a second stored field.
    time_start = fields.Float(string="Start Time", copy=False)
    # Elevata code and views use time_end while hr_timesheet_begin_end owns
    # time_stop. Keep time_end as a writable alias so both names agree.
    time_end = fields.Float(string="End Time", copy=False)

    datetime_start = fields.Datetime(
        string="Start DateTime",
        compute='_compute_datetime_fields',
        inverse='_inverse_datetime_fields',
        store=True,
    )
    datetime_end = fields.Datetime(
        string="End DateTime",
        compute='_compute_datetime_fields',
        inverse='_inverse_datetime_fields',
        store=True,
    )

    calendar_event_id = fields.Many2one(
        'calendar.event',
        string="Calendar Event",
        ondelete='set null',
        copy=False,
    )

    # ── Computed fields ──

    @api.depends('date', 'time_start', 'time_stop')
    def _compute_datetime_fields(self):
        for record in self:
            if not record.date:
                record.datetime_start = False
                record.datetime_end = False
                continue
            user_tz = pytz.timezone(self.env.user.tz or 'UTC')
            start = record.time_start or 0.0
            stop = record.time_stop or 0.0
            record.datetime_start = self._float_time_to_utc(record.date, start, user_tz)
            record.datetime_end = self._float_time_to_utc(record.date, stop, user_tz)

    @api.model
    def _float_time_to_utc(self, day, float_time, user_tz):
        """Turn a wall-clock float on ``day`` into a naive UTC datetime."""
        hours = int(float_time)
        minutes = int(round((float_time - hours) * 60))
        local = user_tz.localize(
            datetime.combine(day, datetime.min.time()).replace(
                hour=hours, minute=minutes
            )
        )
        return local.astimezone(pytz.UTC).replace(tzinfo=None)

    def _inverse_datetime_fields(self):
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        for record in self:
            # Build both values first and write them in one go. Writing
            # time_stop before time_start would trip hr_timesheet_begin_end's
            # "beginning hour must precede ending hour" check mid-update.
            vals = {}
            for dt_field, float_field in (
                ('datetime_start', 'time_start'),
                ('datetime_end', 'time_stop'),
            ):
                value = record[dt_field]
                if not value:
                    continue
                local = pytz.UTC.localize(value).astimezone(user_tz)
                vals[float_field] = local.hour + local.minute / 60.0
                if not record.date:
                    vals['date'] = local.date()
            if vals:
                record.write(vals)

    # ── time_end alias ──

    def _sync_time_end_alias(self, vals):
        """Mirror time_end <-> time_stop so callers may use either name."""
        if 'time_end' in vals and 'time_stop' not in vals:
            vals['time_stop'] = vals['time_end']
        elif 'time_stop' in vals and 'time_end' not in vals:
            vals['time_end'] = vals['time_stop']
        return vals

    @api.onchange('time_end')
    def _onchange_time_end(self):
        self.time_stop = self.time_end

    # ── Validation ──

    @api.constrains('time_start', 'time_stop')
    def _check_time_validity(self):
        for record in self:
            # 0.0 is falsy, so a half-filled record (only time_start set)
            # used to be validated against time_end = 0 and rejected with
            # "beginning hour must precede ending hour". Validate only when
            # both ends carry a real value.
            if record.time_start > 0 and record.time_stop > 0:
                if record.time_start >= record.time_stop:
                    raise ValidationError(_("Start time must be before end time"))
                if record.time_start < 0 or record.time_start >= 24:
                    raise ValidationError(_("Start time must be between 0 and 24"))
                if record.time_stop < 0 or record.time_stop > 24:
                    raise ValidationError(_("End time must be between 0 and 24"))

    @api.constrains('time_start', 'time_stop')
    def _check_interval(self):
        for record in self:
            for value, label in (
                (record.time_start, _("Start time")),
                (record.time_stop, _("End time")),
            ):
                if not value:
                    continue
                minutes = (value % 1) * 60
                if round(minutes) % INTERVAL_MINUTES != 0:
                    raise ValidationError(
                        _(
                            "%(label)s must be on a %(interval)s minute "
                            "interval (00, 15, 30, 45).",
                            label=label,
                            interval=INTERVAL_MINUTES,
                        )
                    )

    # ── Onchange ──

    @api.onchange('time_start', 'time_stop')
    def _onchange_times(self):
        if self.time_start and self.time_end:
            self.unit_amount = round(self.time_end - self.time_start, 2)
