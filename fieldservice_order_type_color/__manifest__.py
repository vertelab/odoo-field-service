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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Field Service: Order Type Color',
    'summary': 'Color coding on field service order types.',
    'category': 'Field Service',
    'author': 'Vertel Sverige AB',
    'contributor': '',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'version': '18.0.1.0.2',
    # Version ledger: 18.0 = Odoo version. 1 = Major. Non regressionable code.
    # 0 = Minor. 1 = Bug fixes
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_order_type_color',
    'description': '''
Field Service: Order Type Color
===============================

    Adds a colour to `fieldservice.order.type` so order types can be told
    apart at a glance in lists and kanban.

    Ported from Elevata's `elevata_order_types`. Two things changed in the
    port:

    - The model is `fieldservice.order.type`, not OCA's `fsm.order.type`.
      Our field service fork replaced the OCA model, so the inheritance
      target moved with it.
    - The colour is a proper `Char` field with a colour widget, and the
      seed data uses the same xmlids as before so existing references keep
      working.

    Features:

        - Colour picker on the order type form
        - Colour column in the list view
        - Nine seeded order types for elevator service work
    ''',
    'depends': [
        'fieldservice_vrtl',
    ],
    'data': [
        'views/fieldservice_order_type_views.xml',
        'data/fieldservice_order_type_data.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
