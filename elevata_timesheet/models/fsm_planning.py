from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from datetime import datetime, timedelta
import pytz


class ElevataFsmPlanning(models.Model):
    _name = 'elevata.fsm.planning'
    _description = 'FSM Planning Line'
    _order = 'date_start'

    fsm_order_id = fields.Many2one(
        'fieldservice.order', string="Work Order",
        required=True, ondelete='cascade', index=True,
    )
    requested_employee_ids = fields.Many2one('hr.employee', string="Technician")
    planning_date = fields.Date(string="Date", required=True)
    time_start = fields.Float(string="Start Time")
    time_end = fields.Float(string="End Time")
    date_start = fields.Datetime(
        string="Start",
        compute='_compute_datetime_fields',
        store=True,
        index=True,
    )
    date_stop = fields.Datetime(
        string="End",
        compute='_compute_datetime_fields',
        store=True,
    )
    is_confirmed = fields.Boolean(
        string="Confirmed with Customer", default=False,
    )
    note = fields.Char(string="Note")
    calendar_event_id = fields.Many2one(
        'calendar.event', string="Calendar Event",
        ondelete='set null', copy=False,
    )

    # ── Compute datetime from date + time ──

    @api.depends('planning_date', 'time_start', 'time_end')
    def _compute_datetime_fields(self):
        for rec in self:
            if not rec.planning_date:
                rec.date_start = False
                rec.date_stop = False
                continue
            user_tz = pytz.timezone(self.env.user.tz or 'UTC')
            base_date = datetime.combine(rec.planning_date, datetime.min.time())
            if rec.time_start is not False and rec.time_start is not None:
                hours = int(rec.time_start)
                minutes = int(round((rec.time_start % 1) * 60))
                local_dt = base_date + timedelta(hours=hours, minutes=minutes)
                utc_dt = user_tz.localize(local_dt).astimezone(pytz.UTC)
                rec.date_start = utc_dt.replace(tzinfo=None)
            else:
                rec.date_start = False
            if rec.time_end is not False and rec.time_end is not None:
                hours = int(rec.time_end)
                minutes = int(round((rec.time_end % 1) * 60))
                local_dt = base_date + timedelta(hours=hours, minutes=minutes)
                utc_dt = user_tz.localize(local_dt).astimezone(pytz.UTC)
                rec.date_stop = utc_dt.replace(tzinfo=None)
            else:
                rec.date_stop = False

    @api.onchange('time_start', 'time_end', 'planning_date')
    def _onchange_planning_times(self):
        if self.planning_date and self.time_start and self.time_end:
            if self.time_start >= self.time_end:
                return {'warning': {
                    'title': _("Warning"),
                    'message': _("Starttid måste vara före sluttid"),
                }}

    # ── Convert to timesheet ──

    def action_convert_to_timesheet(self):
        self.ensure_one()
        order = self.fsm_order_id
        if not order:
            raise ValidationError(_("Planeringsraden saknar arbetsorder."))
        project = self.env.ref(
            'elevata_timesheet.project_fsm_faltservice',
            raise_if_not_found=False,
        )
        employee = self.requested_employee_ids or False
        ts_vals = {
            'date': self.planning_date,
            'time_start': self.time_start,
            'time_end': self.time_end,
            'unit_amount': round(self.time_end - self.time_start, 2) if self.time_end and self.time_start else 0,
            'employee_id': employee.id if employee else False,
            'fsm_order_id': order.id,
            'project_id': project.id if project else False,
            'name': self.note or order.name or '',
        }
        self.env['account.analytic.line'].create(ts_vals)
        self.unlink()
        return True

    def _get_calendar_tag(self):
        self.ensure_one()
        if self.is_confirmed:
            return self.env.ref(
                'elevata_base.calendar_tag_planned_booked',
                raise_if_not_found=False,
            )
        return self.env.ref(
            'elevata_base.calendar_tag_planned_unbooked',
            raise_if_not_found=False,
        )

    def _prepare_calendar_event_vals(self):
        self.ensure_one()
        order = self.fsm_order_id
        location_name = order.equipment_id.name if order.equipment_id else ''
        order_type_str = order.type.name if order.type else ''
        name_parts = [p for p in [order.name, order_type_str, location_name] if p]
        event_name = _('Planning') + ' — ' + ' | '.join(name_parts) if name_parts else _('Planned Order')

        partner_ids = []
        if self.requested_employee_ids and self.requested_employee_ids.user_id and self.requested_employee_ids.user_id.partner_id:
            partner_ids.append(self.requested_employee_ids.user_id.partner_id.id)

        tag = self._get_calendar_tag()
        categ_ids = [(6, 0, [tag.id])] if tag else [(5, 0, 0)]

        status = _('Confirmed') if self.is_confirmed else _('Not confirmed')
        tech = self.requested_employee_ids.name if self.requested_employee_ids else _('No technician')
        customer_name = ''
        if order.equipment_id and order.equipment_id.customer_id:
            customer_name = order.equipment_id.customer_id.name or ''
        desc_parts = [order.name or '', order_type_str, location_name, customer_name, tech, status]
        description = ' | '.join(p for p in desc_parts if p)

        return {
            'name': event_name,
            'start': self.date_start,
            'stop': self.date_stop,
            'partner_ids': [(6, 0, partner_ids)],
            'categ_ids': categ_ids,
            'description': description,
            'elevata_fsm_order_id': order.id if order else False,
        }

    def _sync_to_calendar(self):
        for line in self:
            vals = line._prepare_calendar_event_vals()
            if line.calendar_event_id:
                line.calendar_event_id.with_context(
                    no_calendar_sync_back=True
                ).write(vals)
            else:
                event = self.env['calendar.event'].with_context(
                    no_calendar_sync_back=True
                ).create(vals)
                line.calendar_event_id = event.id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_to_calendar()
        records.mapped('fsm_order_id')._auto_assign_stage()
        return records

    def write(self, vals):
        res = super().write(vals)
        sync_fields = {
            'planning_date', 'time_start', 'time_end', 'requested_employee_ids',
            'is_confirmed', 'note', 'fsm_order_id',
        }
        if sync_fields & set(vals.keys()):
            self._sync_to_calendar()
        return res

    def unlink(self):
        orders = self.mapped('fsm_order_id')
        for line in self:
            if line.calendar_event_id:
                line.calendar_event_id.with_context(
                    no_calendar_sync_back=True
                ).unlink()
        res = super().unlink()
        orders._auto_assign_stage()
        return res
