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
    fieldservice_order_line_employee_ids = fields.One2many('fieldservice.order.line.employee', 'fieldservice_order_line_id', string='Employees')
    

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

    def open_form_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fieldservice.order.line',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # date_start = fields.Datetime(string='Start Date', group_expand='_read_group_date_start_day')


        # logging.warning(f"{domain=}")
        # logging.warning(f"{fields=}")
        # logging.warning(f"{groupby=}")
        # logging.warning(f"{offset=}")
        # logging.warning(f"{limit=}")
        # logging.warning(f"{orderby=}")
        # logging.warning(f"{lazy=}")
    
    # @api.model
    # def _read_group_date_start_day(self, dates, domain, order):
    #     today = fields.Date.today()
    #     result = []
    #     for i in range(365):
    #         current_date = today + timedelta(days=i)
    #         result.append({
    #             'id': i,  # Add a unique identifier
    #             'date_start': current_date.strftime('%Y-%m-%d'),
    #             'date_start_count': 0,
    #             '__domain': [('date_start', '>=', current_date.strftime('%Y-%m-%d 00:00:00')),
    #                         ('date_start', '<', (current_date + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00'))]
    #         })
    #     return result


    # @api.model
    # def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
    #     if groupby and groupby[0] == 'date_start:day':
    #         return self._read_group_date_start_day(None, domain, orderby)
    #     return super(FieldServiceOrderLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
    