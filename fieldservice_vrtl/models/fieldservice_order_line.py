from odoo import api, fields, models, _
from datetime import date as date_type
from datetime import datetime, timedelta
from odoo.tools import date_utils
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)


class FieldServiceOrderLine(models.Model):
    _name = 'fieldservice.order.line'
    _description = 'Field Service Order Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_id = fields.Many2one('fieldservice.order', string='Service Order', required=True)
    stage_id = fields.Many2one('fieldservice.stage', string='Stage', tracking=True)
    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date')
    image_ids = fields.Many2many('ir.attachment', string='Images')
    priority = fields.Selection(related="order_id.priority")
    address = fields.Char(related="order_id.address")

    date_day_start_char = fields.Char(compute="_compute_date_chars",store=True, readonly=False, inverse="_inverse_date_day_start_char", group_expand='_read_group_days')
    date_week_start_char = fields.Char(compute="_compute_date_chars",store=True, readonly=False, inverse="_inverse_date_week_start_char", group_expand='_read_group_weeks')
    # date_month_start_char = fields.Char(compute="compute_from_start",store=True, readonly=False)
    # date_year_start_char = fields.Char(compute="compute_from_start",store=True, readonly=False)
    duration = fields.Float(string='Duration', compute='_compute_duration', store=True, help='Duration in hours')
    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        related="order_id.company_id"
    )
    custom_state = fields.Selection([
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('red', 'Red')
    ], string='Custom State', compute='_compute_custom_state', store=True)

    @api.model
    def _read_group_days(self, groupby, domain, limit=None, offset=None):
        today = date.today()
        num_to_month = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"]
        days = [f"{(today + timedelta(days=i)).day} {num_to_month[(today + timedelta(days=i)).month-1]} {(today + timedelta(days=i)).year}" for i in range(5)]
        return days[:5] 

    @api.model
    def _read_group_weeks(self, groupby, domain, limit=None, offset=None):
        today = date.today()
        weeks = [f"W{str((today + timedelta(weeks=i)).isocalendar().week).zfill(2)} {(today + timedelta(weeks=i)).year}" for i in range(5)]
        return weeks[:5] 



    @api.depends('date_start')
    def _compute_date_chars(self):
        num_to_month = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"]
        for record in self:
            if record.date_start:
                record.date_day_start_char = f"{record.date_start.day} {num_to_month[record.date_start.month-1]} {record.date_start.year}"
                record.date_week_start_char = f"W{str(record.date_start.isocalendar().week).zfill(2)} {record.date_start.year}"
            else:
                record.date_day_start_char = False
                record.date_week_start_char = False


    def _inverse_date_day_start_char(self):
        num_to_month = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"]
        for record in self:
            if record.date_day_start_char:
                day, month, year = record.date_day_start_char.split(" ")
                new_date = datetime(int(year), num_to_month.index(month) + 1, int(day))
                if record.date_start:
                    new_date = new_date.replace(hour=record.date_start.hour, minute=record.date_start.minute, second=record.date_start.second)
                record.date_start = new_date

    def _inverse_date_week_start_char(self):
        for record in self:
            if record.date_week_start_char:
                week, year = record.date_week_start_char[1:].split()
                jan_1 = datetime(int(year), 1, 1)
                new_date = jan_1 + relativedelta(weeks=int(week) - 1, weekday=0)
                if record.date_start:
                    new_date = new_date.replace(hour=record.date_start.hour, minute=record.date_start.minute, second=record.date_start.second)
                record.date_start = new_date

    @api.onchange('date_start', 'duration')
    def _onchange_date_start_duration(self):
        if self.date_start:
            if self.duration:
                self.date_end = self.date_start + timedelta(hours=self.duration)
            elif self.date_end:
                time_diff = self.date_end - self.date_start
                self.date_end = self.date_start + time_diff

    @api.onchange('date_end')
    def _onchange_date_end(self):
        if self.date_start and self.date_end:
            self.duration = (self.date_end - self.date_start).total_seconds() / 3600

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for line in self:
            if line.date_start and line.date_end:
                line.duration = (line.date_end - line.date_start).total_seconds() / 3600
            else:
                line.duration = 0.0
        self._compute_custom_state()

    def write(self, vals):
        if 'date_start' in vals and 'date_end' not in vals and 'duration' not in vals:
            for record in self:
                new_start = fields.Datetime.to_datetime(vals['date_start'])
                if record.duration:
                    vals['date_end'] = new_start + timedelta(hours=record.duration)
        return super(FieldServiceOrderLine, self).write(vals)

    @api.depends('duration')
    def _compute_custom_state(self):
        MAX_HOURS = 40
        groups = self.read_group([], ['custom_state', 'duration:sum'], ['custom_state'])
        state_totals = {group['custom_state']: group['duration'] for group in groups}
        
        for record in self:
            total_duration = state_totals.get(record.custom_state, 0)
            usage_percentage = (total_duration / MAX_HOURS) * 100
            if usage_percentage <= 40:
                record.custom_state = 'green'
            elif 40 < usage_percentage <= 80:
                record.custom_state = 'yellow'
            else:
                record.custom_state = 'red'


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if 'date_start' in groupby:
            date_start_field = self._fields['date_start']
            is_datetime = date_start_field.type == 'datetime'
            min_record = self.search(domain + [('date_start', '!=', False)], order='date_start asc', limit=1)
            max_record = self.search(domain + [('date_end', '!=', False)], order='date_end desc', limit=1)

            if min_record and max_record:
                min_date = min_record.date_start
                max_date = max_record.date_end

                if is_datetime:
                    min_date = min_date.date()
                    max_date = max_date.date()

                date_range = list(date_utils.date_range(min_date, max_date, step=timedelta(days=1)))
                date_range = [d.strftime('%Y-%m-%d') for d in date_range[:5]] 

                result = super(FieldServiceOrderLine, self).read_group(
                    domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy,
                    expand='date_start', expand_dates=True, expand_values=date_range
                )
                return result[:5]

        elif 'date_day_start_char' in groupby:
            allowed_days = self._read_group_days(groupby, domain)
            result = super(FieldServiceOrderLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
            return [r for r in result if r.get('date_day_start_char') in allowed_days][:5]

        elif 'date_week_start_char' in groupby:
            allowed_weeks = self._read_group_weeks(groupby, domain)
            result = super(FieldServiceOrderLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
            return [r for r in result if r.get('date_week_start_char') in allowed_weeks][:5]

        return super(FieldServiceOrderLine, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )


    def open_planning_view(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fieldservice.order.line',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('fieldservice_vrtl.view_fieldservice_order_line_form_planning').id,
            'target': 'new',
            'name': 'Planning',
        }

    def open_reporting_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fieldservice.order.line',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('fieldservice_vrtl.view_fieldservice_order_line_form_reporting').id,
            'target': 'new',
            'name': 'Reporting',
        }

