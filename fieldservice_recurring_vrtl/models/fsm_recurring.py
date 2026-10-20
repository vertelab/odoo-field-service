# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FsmRecurring(models.Model):
    """Recurrence template for field service orders.

    A template carries the interval and the data to copy onto each
    generated order. ``next_date`` is the date of the next order to
    create; ``_generate_orders()`` walks it forward.
    """

    _name = 'fsm.recurring'
    _description = 'Recurring Field Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'next_date, id'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)

    # What to generate. The order type is not a field on fieldservice.order
    # in the Vertel fork — it is reached through the product template
    # (product_tmpl_id.product_type). We therefore store the product.
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product',
        tracking=True,
        help='Product whose order type is stamped on generated orders.',
    )
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipment',
        tracking=True,
        help='The elevator the recurring orders concern.',
    )
    requested_employee_ids = fields.Many2many(
        'hr.employee',
        string='Technicians',
        help='Assigned technicians on generated orders.',
    )
    description = fields.Text()

    # Schedule
    interval = fields.Integer(
        string='Interval',
        default=1,
        required=True,
        help='Number of units between two orders.',
    )
    unit = fields.Selection(
        [
            ('day', 'Days'),
            ('week', 'Weeks'),
            ('month', 'Months'),
            ('year', 'Years'),
        ],
        string='Unit',
        default='month',
        required=True,
    )
    next_date = fields.Date(
        string='Next Order Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help='Date of the next order to generate.',
    )
    last_date = fields.Date(
        string='Last Generated',
        readonly=True,
        copy=False,
    )

    order_ids = fields.One2many(
        'fieldservice.order',
        'fsm_recurring_id',
        string='Generated Orders',
        readonly=True,
    )
    order_count = fields.Integer(
        compute='_compute_order_count',
        string='Orders',
    )

    @api.depends('order_ids')
    def _compute_order_count(self):
        for rec in self:
            rec.order_count = len(rec.order_ids)

    def _next_date(self, from_date):
        """Return the date one interval after ``from_date``."""
        self.ensure_one()
        delta = relativedelta(**{f'{self.unit}s': self.interval})
        return from_date + delta

    def _prepare_order_values(self):
        """Values for one generated order.

        Only fields that exist on fieldservice.order in the Vertel fork
        are set here. ``property_id`` is computed from
        ``equipment_id.property_id`` by fieldservice_maintenance_vrtl and
        must not be written.
        """
        self.ensure_one()
        return {
            'fsm_recurring_id': self.id,
            'name': self.name,
            'description': self.description,
            'product_tmpl_id': self.product_tmpl_id.id or False,
            'equipment_id': self.equipment_id.id or False,
            'requested_employee_ids': [(6, 0, self.requested_employee_ids.ids)],
            'planned_start_datetime': self.next_date,
        }

    def _generate_orders(self):
        """Create every order that has come due and advance ``next_date``.

        Idempotent: an order is only created when ``next_date`` is today
        or earlier, and ``next_date`` is then advanced past today. Running
        twice in a row therefore creates nothing the second time.

        At most one order is created per template per run — a template
        left far in the past must not backfill years of history.
        """
        today = fields.Date.context_today(self)
        created = self.env['fieldservice.order']
        for rec in self:
            if not rec.next_date or rec.next_date > today:
                continue
            order = self.env['fieldservice.order'].create(
                rec._prepare_order_values()
            )
            rec.write({
                'last_date': rec.next_date,
                'next_date': rec._next_date(rec.next_date),
            })
            created |= order
            order.message_post(
                body=_('Generated from recurring template %s.') % rec.name
            )
        return created

    def action_generate_orders(self):
        """Button: generate due orders now."""
        created = self._generate_orders()
        if not created:
            raise UserError(
                _('No order is due. The next one is scheduled for %s.')
                % (self.next_date or _('an unspecified date'))
            )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Orders'),
            'res_model': 'fieldservice.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created.ids)],
        }

    def action_view_orders(self):
        """Button: show all orders generated from this template."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Orders'),
            'res_model': 'fieldservice.order',
            'view_mode': 'list,form',
            'domain': [('fsm_recurring_id', '=', self.id)],
            'context': {'default_fsm_recurring_id': self.id},
        }
