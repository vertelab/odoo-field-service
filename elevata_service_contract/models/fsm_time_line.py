from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

RATE_TYPE = [
    ('normaltid', 'Normal Time (Mon-Fri 07:00-16:00)'),
    ('overtid_1_2h', 'Overtime 1-2 h'),
    ('overtid_2h_plus', 'Overtime after 2 h'),
    ('lordag', 'Saturday'),
    ('sondag_helgdag', 'Sunday/Holiday'),
    ('storhelg', 'Major Holiday'),
    ('beredskap_vardag', 'Standby Weekday'),
    ('beredskap_helg', 'Standby Weekend'),
    ('jourutryckning', 'Emergency Call-out (min 3 h)'),
    ('restid', 'Travel Time'),
    ('servicebil_mil', 'Service Vehicle (SEK/10km)'),
    ('servicebil_tid', 'Service Vehicle Time'),
    ('servicebil_fast', 'Service Vehicle Fixed Fee (SEK)'),
    ('verktygsavgift', 'Tool Fee'),
]


class ElevataFsmTimeLine(models.Model):
    _name = 'elevata.fsm.time.line'
    _description = 'Work Order Time Line'
    _order = 'date, id'

    fsm_order_id = fields.Many2one(
        'fieldservice.order',
        string='Work Order',
        required=True,
        ondelete='cascade',
    )
    requested_employee_ids = fields.Many2one(
        'hr.employee',
        string='Technician',
        index=True,
    )
    calendar_event_id = fields.Many2one(
        'calendar.event',
        string='Calendar Event',
        copy=False,
        ondelete='set null',
    )
    datetime_from = fields.Datetime(
        string='From',
        required=True,
        index=True,
    )
    datetime_to = fields.Datetime(
        string='To',
        required=True,
    )
    date = fields.Date(
        string='Date',
        compute='_compute_date',
        store=True,
        readonly=False,
    )
    technician = fields.Char(string='Technician Note')
    hours = fields.Float(
        string='Hours',
        compute='_compute_hours',
        store=True,
        digits=(10, 2),
    )
    rate_type = fields.Selection(
        RATE_TYPE,
        string='Time Type',
        required=True,
        default='normaltid',
    )
    price_per_hour = fields.Float(
        string='Hourly Rate (SEK/h)',
        digits=(16, 2),
    )
    amount = fields.Float(
        string='Amount',
        compute='_compute_amount',
        store=True,
        digits=(16, 2),
    )
    description = fields.Char(string='Note')

    @api.depends('datetime_from')
    def _compute_date(self):
        for line in self:
            line.date = (
                line.datetime_from.date() if line.datetime_from else False
            )

    @api.depends('datetime_from', 'datetime_to')
    def _compute_hours(self):
        for line in self:
            if (line.datetime_from and line.datetime_to
                    and line.datetime_to > line.datetime_from):
                delta = line.datetime_to - line.datetime_from
                line.hours = delta.total_seconds() / 3600.0
            else:
                line.hours = 0.0

    @api.constrains('datetime_from', 'datetime_to')
    def _check_datetime(self):
        for line in self:
            for dt, label in [
                (line.datetime_from, 'From'),
                (line.datetime_to, 'To'),
            ]:
                if dt and dt.minute % 15 != 0:
                    raise ValidationError(
                        _('%s time must be in 15-minute intervals '
                          '(07:00, 07:15, 07:30, 07:45).') % label
                    )
            if (line.datetime_from and line.datetime_to
                    and line.datetime_to <= line.datetime_from):
                raise ValidationError(
                    _('End time must be after start time.')
                )

    @api.depends('hours', 'price_per_hour')
    def _compute_amount(self):
        for line in self:
            line.amount = line.hours * line.price_per_hour

    @api.onchange('fsm_order_id')
    def _onchange_fsm_order_id(self):
        if (self.fsm_order_id and self.fsm_order_id.requested_employee_ids
                and not self.requested_employee_ids):
            self.requested_employee_ids = self.fsm_order_id.requested_employee_ids

    @api.onchange('rate_type')
    def _onchange_rate_type(self):
        if not self.rate_type or not self.fsm_order_id:
            return
        order = self.fsm_order_id
        contract_type = order.elevata_contract_type
        if not contract_type:
            return
        pricelist = False
        if (order.service_contract_id
                and order.service_contract_id.partner_id):
            pricelist = (
                order.service_contract_id.partner_id.elevata_pricelist_id
            )
        if not pricelist and 'elevata.pricelist' in self.env.registry:
            pricelist = self.env['elevata.pricelist'].search(
                [('active', '=', True)], limit=1, order='id asc'
            )
        if pricelist:
            self.price_per_hour = pricelist.get_rate(self.rate_type)

    def _prepare_calendar_event(self):
        self.ensure_one()
        order = self.fsm_order_id
        rate_label = dict(
            self._fields['rate_type']._description_selection(self.env)
        ).get(self.rate_type, self.rate_type)
        location_name = ''
        if order and order.equipment_id:
            location_name = order.equipment_id.complete_name or ''
        event_name = '%s — %s%s' % (
            order.name if order else '',
            rate_label,
            (' — ' + location_name) if location_name else '',
        )
        model_id = self.env['ir.model']._get(
            'elevata.fsm.time.line'
        ).id
        partner_ids = []
        user_id = self.env.user.id
        if self.requested_employee_ids and self.requested_employee_ids.partner_id:
            partner_ids = [(4, self.requested_employee_ids.partner_id.id)]
            user = self.requested_employee_ids.partner_id.user_ids
            if user:
                user_id = user[0].id
        return {
            'name': event_name,
            'start': self.datetime_from,
            'stop': self.datetime_to,
            'allday': False,
            'res_model_id': model_id,
            'res_id': self.id,
            'user_id': user_id,
            'partner_ids': partner_ids,
        }

    def _sync_to_calendar(self):
        for line in self:
            if not line.datetime_from or not line.datetime_to:
                continue
            vals = line._prepare_calendar_event()
            if line.calendar_event_id:
                line.calendar_event_id.with_context(
                    no_mail_to_attendees=True,
                    recurse_time_line=True,
                ).write({
                    'name': vals['name'],
                    'start': vals['start'],
                    'stop': vals['stop'],
                })
            else:
                event = self.env['calendar.event'].with_context(
                    no_mail_to_attendees=True,
                ).create(vals)
                line.calendar_event_id = event

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_to_calendar()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in (
            'datetime_from', 'datetime_to', 'requested_employee_ids',
            'rate_type', 'fsm_order_id',
        )):
            self._sync_to_calendar()
        return res

    def unlink(self):
        self.mapped('calendar_event_id').unlink()
        return super().unlink()
