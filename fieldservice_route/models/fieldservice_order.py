# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models


class FieldserviceOrder(models.Model):
    """Route fields on the work order.

    The sequence is set by the planner, not computed: automatic route
    optimisation needs a distance matrix, which is an external service or a
    self-hosted OSRM — a deployment decision, not something a module should
    assume. What this does compute is the arrival time, which follows from
    the sequence and the travel times.
    """

    _inherit = 'fieldservice.order'

    routing_sequence = fields.Integer(
        string='Route Stop',
        default=0,
        help='Where in the day this stop falls. 0 = not yet sequenced.',
    )
    estimated_arrival = fields.Datetime(
        string='Estimated Arrival',
        compute='_compute_estimated_arrival',
        store=True,
    )
    travel_time_minutes = fields.Integer(
        string='Travel Time (min)',
        help='Estimated driving time from the previous stop.',
    )
    service_time_minutes = fields.Integer(
        string='Service Time (min)',
        default=60,
        help='How long the visit takes. Used to compute the next arrival.',
    )
    route_date = fields.Date(
        string='Route Date',
        default=fields.Date.context_today,
        index=True,
        help='The day this stop is planned for.',
    )
    street = fields.Char(
        related='partner_id.street',
        string='Street',
        readonly=True,
    )
    city = fields.Char(
        related='partner_id.city',
        string='City',
        readonly=True,
    )

    @api.depends('routing_sequence', 'travel_time_minutes',
                 'service_time_minutes', 'route_date', 'planned_start_datetime')
    def _compute_estimated_arrival(self):
        """Arrival follows from the sequence, within the same day.

        The first stop starts at planned_start_datetime (or 08:00), and each
        following stop adds the previous stop's service time and its own
        travel time. Computed per day and technician, because two
        technicians on the same day have independent routes.
        """
        for order in self:
            if not order.routing_sequence or not order.route_date:
                order.estimated_arrival = False
                continue

            day_start = order.planned_start_datetime or fields.Datetime.to_datetime(
                order.route_date).replace(hour=8, minute=0)

            # Previous stops for the same day and the same technicians.
            domain = [
                ('route_date', '=', order.route_date),
                ('routing_sequence', '>', 0),
                ('routing_sequence', '<', order.routing_sequence),
                ('id', '!=', order.id),
            ]
            if order.requested_employee_ids:
                domain.append(('requested_employee_ids', 'in',
                               order.requested_employee_ids.ids))
            previous = self.search(domain, order='routing_sequence')

            arrival = day_start
            for stop in previous:
                arrival += timedelta(minutes=stop.travel_time_minutes or 0)
                arrival += timedelta(minutes=stop.service_time_minutes or 0)
            arrival += timedelta(minutes=order.travel_time_minutes or 0)
            order.estimated_arrival = arrival

    def action_plan_route(self):
        """Sequence the selected orders in the order they were selected.

        A starting point, not an optimiser: the planner selects the stops in
        the order they want them, and this numbers them and recomputes the
        arrivals. Reordering afterwards is a drag in the list.
        """
        for index, order in enumerate(self, start=1):
            order.routing_sequence = index
        self._compute_estimated_arrival()
        return True

    def action_clear_route(self):
        self.write({'routing_sequence': 0, 'estimated_arrival': False})
        return True
