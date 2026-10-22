# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Field Service: Route',
    'version': '18.0.1.0.0',
    # Version ledger: 18.0 = Odoo version. 1 = Major. Non regressionable code.
    # 0 = Minor. 1 = Bug fixes
    'summary': 'Plan a technician day: route order, travel time, map view.',
    'category': 'Field Service',
    'description': '''
Field Service: Route
====================

    A technician's day, ordered.

    A service company with hundreds of assets in a city does not send a
    technician to one address at a time. It plans a day: five or six stops,
    in an order that minimises driving. Odoo has the work orders and the
    map; what it lacks is the sequence and the travel time between stops.

    Added to fieldservice.order:

        routing_sequence       where in the day this stop falls
        estimated_arrival      when the technician gets there
        travel_time_minutes    from the previous stop
        service_time_minutes   how long the visit takes
        route_date             the day this stop is planned for

    estimated_arrival is computed forward from the day's start: 08:00 plus
    the first stop's travel time, then each following stop adds the previous
    stop's service time and its own travel time. Computed per day and per
    technician — two technicians on the same day have independent routes.

    The sequence is set by the planner, not optimised. Automatic route
    optimisation needs a distance matrix: an external service or a
    self-hosted OSRM. That is a deployment decision, not something a module
    should assume. A company that later adds a routing service can fill the
    sequence automatically and the rest of the module does not change.

    Features:

        - Route sequence, ETA and travel time on work orders
        - Arrival times computed forward from a day's start
        - Map view of the day's stops in order
        - "Plan route" action that sequences the selected orders
    ''',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_route',
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'depends': [
        'fieldservice_vrtl',
        'web_map_ce',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fieldservice_order_views.xml',
        'views/route_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
