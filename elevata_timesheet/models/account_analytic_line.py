from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.elevata_base.constants import RATE_TYPE

import pytz


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    name = fields.Char(required=False)

    # time_start / time_end / datetime_start / datetime_end /
    # calendar_event_id and the 15 minute grid validation live in
    # fieldservice_timesheet_vrtl. This module only adds what is Elevata
    # specific: the rate type and the price it resolves to.

    rate_type = fields.Selection(
        RATE_TYPE,
        string="Rate Type",
        default='normaltid',
    )
    price_per_hour = fields.Float(string="Price per Hour", digits=(16, 2))
    amount_elevata = fields.Float(
        string="Amount",
        compute='_compute_amount_elevata',
        store=True,
        digits=(16, 2),
    )

    # ── Computed fields ──

    @api.depends('unit_amount', 'price_per_hour')
    def _compute_amount_elevata(self):
        for line in self:
            line.amount_elevata = line.unit_amount * line.price_per_hour

    # ── Constraints ──

    def _get_rate_price(self):
        self.ensure_one()
        order = self.fsm_order_id
        if not order or not self.rate_type:
            return 0.0
        pricelist = False
        if order.service_contract_id and order.service_contract_id.partner_id:
            pricelist = order.service_contract_id.partner_id.elevata_pricelist_id
        if not pricelist and 'elevata.pricelist' in self.env.registry:
            pricelist = self.env['elevata.pricelist'].sudo().search(
                [('active', '=', True)], limit=1, order='id asc'
            )
        return pricelist.sudo().get_rate(self.rate_type) if pricelist else 0.0

    def _fill_rate_price(self):
        for line in self.filtered(
            lambda l: l.fsm_order_id and l.rate_type and not l.price_per_hour
        ):
            line.price_per_hour = line._get_rate_price()

    @api.onchange('rate_type', 'fsm_order_id')
    def _onchange_rate_type_price(self):
        if not self.fsm_order_id or not self.rate_type:
            return
        self.price_per_hour = self._get_rate_price()

    # ── Calendar sync ──

    def _get_calendar_tag(self):
        order = self.fsm_order_id
        if order and order.stage_id and order.stage_id.is_closed:
            return self.env.ref(
                'elevata_base.calendar_tag_locked_timesheet',
                raise_if_not_found=False,
            )
        return self.env.ref(
            'elevata_base.calendar_tag_open_timesheet',
            raise_if_not_found=False,
        )

    def _prepare_calendar_event_vals(self):
        self.ensure_one()
        if not self.datetime_start or not self.datetime_end:
            return False
        order_name = self.fsm_order_id.name if self.fsm_order_id else ''
        location_name = ''
        if self.fsm_order_id and self.fsm_order_id.equipment_id:
            location_name = self.fsm_order_id.equipment_id.name
        order_type_str = ''
        if self.fsm_order_id and self.fsm_order_id.type:
            order_type_str = self.fsm_order_id.type.name or ''
        name_parts = [p for p in [order_name, order_type_str, location_name] if p]
        event_name = _('Timesheet') + ' — ' + ' | '.join(name_parts) if name_parts else _('Timesheet')

        partner_ids = []
        if self.employee_id and self.employee_id.user_id and self.employee_id.user_id.partner_id:
            partner_ids.append(self.employee_id.user_id.partner_id.id)

        tag = self._get_calendar_tag()
        categ_ids = [(6, 0, [tag.id])] if tag else [(5, 0, 0)]

        customer_name = ''
        if self.fsm_order_id and self.fsm_order_id.equipment_id and self.fsm_order_id.equipment_id.customer_id:
            customer_name = self.fsm_order_id.equipment_id.customer_id.name or ''

        rate_label = dict(
            self._fields['rate_type']._description_selection(self.env)
        ).get(self.rate_type, '')
        desc_parts = [order_name, order_type_str, location_name, customer_name, rate_label]
        description = ' | '.join(p for p in desc_parts if p)

        return {
            'name': event_name,
            'start': self.datetime_start,
            'stop': self.datetime_end,
            'partner_ids': [(6, 0, partner_ids)],
            'categ_ids': categ_ids,
            'description': description,
            'elevata_fsm_order_id': self.fsm_order_id.id if self.fsm_order_id else False,
        }

    def _sync_to_calendar(self):
        for line in self:
            vals = line._prepare_calendar_event_vals()
            if not vals:
                if line.calendar_event_id:
                    line.calendar_event_id.unlink()
                    line.calendar_event_id = False
                continue
            if line.calendar_event_id:
                line.calendar_event_id.with_context(no_calendar_sync_back=True).write(vals)
            else:
                event = self.env['calendar.event'].with_context(
                    no_calendar_sync_back=True
                ).create(vals)
                line.calendar_event_id = event.id

    # ── Analytic helpers ──

    def _get_fsm_project(self):
        return self.env.ref(
            'elevata_timesheet.project_fsm_faltservice',
            raise_if_not_found=False,
        )

    def _get_fsm_analytic_vals(self):
        self.ensure_one()
        vals = {}
        order = self.fsm_order_id
        if not order:
            return vals
        if order.type and order.type.verksamhetstyp_analytic_id:
            vals['x_plan4_id'] = order.type.verksamhetstyp_analytic_id.id
        falt_tekniker = self.env['account.analytic.account'].search([
            ('plan_id', '=', 5),
            ('name', '=', 'Fält \u2014 Tekniker'),
        ], limit=1)
        if falt_tekniker:
            vals['x_plan5_id'] = falt_tekniker.id
        hissobjekt_plan = self.env.ref(
            'elevata_timesheet.analytic_plan_hissobjekt',
            raise_if_not_found=False,
        )
        if hissobjekt_plan and order.equipment_id:
            field_name = f'x_plan{hissobjekt_plan.id}_id'
            if field_name in self._fields:
                analytic = order.equipment_id.elevata_hiss_analytic_id
                if not analytic:
                    analytic = order.equipment_id._get_or_create_analytic_account()
                if analytic:
                    vals[field_name] = analytic.id
        return vals

    def _ensure_fsm_project(self):
        project = self._get_fsm_project()
        for line in self.filtered('fsm_order_id'):
            update_vals = {}
            if project and not line.project_id:
                update_vals['project_id'] = project.id
            analytic_vals = line._get_fsm_analytic_vals()
            update_vals.update({k: v for k, v in analytic_vals.items() if not line[k]})
            if update_vals:
                line.with_context(no_calendar_sync_back=True).write(update_vals)

    # ── CRUD overrides ──

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._sync_time_end_alias(dict(v)) for v in vals_list]
        project = self._get_fsm_project()
        for vals in vals_list:
            if vals.get('fsm_order_id') and not vals.get('project_id') and project:
                vals['project_id'] = project.id
            # hr_timesheet_begin_end validates unit_amount == time_stop - time_start
            # inside super().create(), so it must be correct before the call.
            start, stop = vals.get('time_start'), vals.get('time_stop')
            if start is not None and stop is not None and stop >= start:
                # project_timesheet_time_control sets date_time from date and
                # then recomputes unit_amount from date_time..date_time_end.
                # Give it the real start/stop so the recomputation agrees with
                # hr_timesheet_begin_end's constraint.
                day = vals.get('date') or fields.Date.context_today(self)
                base = datetime.combine(fields.Date.to_date(day), datetime.min.time())
                vals['unit_amount'] = round(stop - start, 2)
                vals['time_end'] = stop
                vals['date_time'] = base + timedelta(hours=start)
                vals['date_time_end'] = base + timedelta(hours=stop)
        records = super().create(vals_list)
        # hr_timesheet._split_amount_fname() returns unit_amount when the line
        # has a project, and the core upsert then recomputes it from the
        # quantity split. Re-assert the value from the hours afterwards so
        # hr_timesheet_begin_end's constraint (unit_amount == stop - start)
        # still holds for project lines.
        for record in records:
            if record.time_start and record.time_stop and record.unit_amount != round(
                    record.time_stop - record.time_start, 2):
                super(AccountAnalyticLine, record).write({
                    'unit_amount': round(record.time_stop - record.time_start, 2),
                })
        records._fill_rate_price()
        records.filtered('fsm_order_id')._ensure_fsm_project()
        records.filtered(lambda r: r.datetime_start and r.datetime_end)._sync_to_calendar()
        orders = records.filtered('fsm_order_id').mapped('fsm_order_id')
        if orders:
            orders._auto_assign_stage()
        return records

    def write(self, vals):
        vals = self._sync_time_end_alias(dict(vals))
        res = super().write(vals)
        if 'price_per_hour' not in vals and ('rate_type' in vals or 'fsm_order_id' in vals):
            self._fill_rate_price()
        if 'fsm_order_id' in vals:
            self._ensure_fsm_project()
        sync_fields = {'date', 'time_start', 'time_stop', 'name', 'employee_id', 'rate_type', 'fsm_order_id'}
        if sync_fields & set(vals.keys()):
            self.filtered(lambda r: r.datetime_start and r.datetime_end)._sync_to_calendar()
        return res

    def unlink(self):
        orders = self.filtered('fsm_order_id').mapped('fsm_order_id')
        events = self.mapped('calendar_event_id').filtered(lambda e: e.exists())
        res = super().unlink()
        events.unlink()
        if orders:
            orders._auto_assign_stage()
        return res
