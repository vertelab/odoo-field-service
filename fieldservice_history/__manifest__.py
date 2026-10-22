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
    'name': 'Field Service: History',
    'version': '18.0.1.0.6',
    # Version ledger: 18.0 = Odoo version. 1 = Major. Non regressionable code.
    # 0 = Minor. 1 = Bug fixes
    'summary': 'Order history per asset, and a completed date that survives.',
    'category': 'Field Service',
    'description': '''
Field Service: History
=======================

    What happened to this asset before, and when was the last order closed?

    Split out of elevata_fsm_order_history, which was entirely generic —
    nothing in it was elevator-specific.

    Two things:

    date_completed
        Stamped when the order enters a closed stage, and never touched
        again. Odoo has date_end, but that is the planned end; the date a
        job was actually finished is what a service history is built on,
        and what a warranty claim is measured from.

    Related orders
        Every other order on the same asset, newest first, plus a count of
        the ones still open. A technician arriving at an asset wants to
        know what was done last time and whether something is still
        outstanding — without running a search.

    The asset is maintenance.equipment, which is where fieldservice.order
    gets equipment_id from fieldservice_maintenance.

    Features:

        - date_completed stamped on stage change, read-only afterwards
        - Related orders on the order, newest first
        - Active order count on the asset
        - Smart buttons on both forms
    ''',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_history',
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'depends': [
        'fieldservice_vrtl',
        'fieldservice_maintenance',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fsm_order_views.xml',
        'views/maintenance_equipment_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
