from odoo import api, fields, models, _
from datetime import date as date_type
from datetime import datetime, timedelta
from odoo.tools import date_utils
import logging
from datetime import date, timedelta


class FieldServiceOrderLine(models.Model):
    _name = 'fieldservice.order.line'
    _description = 'Field Service Order Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_id = fields.Many2one('fieldservice.order', string='Service Order', required=True)
    stage_id = fields.Many2one('fieldservice.stage', string='Stage', tracking=True)
    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date')
    image_ids = fields.Many2many('ir.attachment', string='Images')

    date_day_start_char = fields.Char(compute="compute_from_start",store=True, readonly=False, inverse="date_from_char_day")
    date_week_start_char = fields.Char(compute="compute_from_start",store=True, readonly=False, inverse="date_from_char_week")
    # date_month_start_char = fields.Char(compute="compute_from_start",store=True, readonly=False)
    # date_year_start_char = fields.Char(compute="compute_from_start",store=True, readonly=False)

    @api.depends('date_start')
    def compute_from_start(self):
        num_to_month = ["januari", "februari", "mars", "april", "maj", "juni","juli", "augusti", "september", "oktober", "november", "december"]
        for record in self:
            record.date_day_start_char = f"{record.date_start.day} {num_to_month[record.date_start.month-1]} {record.date_start.year}"
            record.date_week_start_char = f"W{str(record.date_start.isocalendar().week).zfill(2)} {record.date_start.year}" 

    def date_from_char_day(self):
        num_to_month = ["januari", "februari", "mars", "april", "maj", "juni","juli", "augusti", "september", "oktober", "november", "december"]
        for record in self:
            day, month, year = record.date_day_start_char.split(" ")
            date_string = f"{year}-{str(num_to_month.index(month)+1).zfill(2)}-{str(day).zfill(2)}"
            record.date_start = date_string

    def date_from_char_week(self):
        for record in self:
            week, year = record.date_week_start_char.split()
            jan_1 = datetime(int(year), 1, 1)
            record.date_start = (jan_1 + timedelta(days=(7 - jan_1.weekday()) % 7) + timedelta(weeks=int(week[1:]) - 1)).date()


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):


        if 'date_start' in groupby:
            date_start_field = self._fields['date_start']
            is_datetime = date_start_field.type == 'datetime'
            logging.warning("read_group if case")
            # Find the minimum and maximum dates in the current domain
            min_record = self.search(domain + [('date_start', '!=', False)], order='date_start asc', limit=1)
            max_record = self.search(domain + [('date_end', '!=', False)], order='date_end desc', limit=1)

            if min_record and max_record:
                min_date = min_record.date_start
                max_date = max_record.date_end

                if is_datetime:
                    min_date = min_date.date()
                    max_date = max_date.date()

                # Generate a list of dates, limiting to a reasonable range (e.g., 366 days)
                date_range = list(date_utils.date_range(min_date, max_date, step=timedelta(days=1)))
                date_range = [d.strftime('%Y-%m-%d') for d in date_range[:366]]


                # Use the expand parameter to include all dates
                return super(FieldServiceOrderLine, self).read_group(
                    domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy,
                    expand='date_start', expand_dates=True, expand_values=date_range
                )

        return super(FieldServiceOrderLine, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )


    def open_planning_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fieldservice.order.line',  # or a different model for planning
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


