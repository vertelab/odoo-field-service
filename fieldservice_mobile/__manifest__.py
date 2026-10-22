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
    'name': 'Field Service: Mobile',
    'version': '18.0.1.0.0',
    # Version ledger: 18.0 = Odoo version. 1 = Major. Non regressionable code.
    # 0 = Minor. 1 = Bug fixes
    'summary': 'Technician mobile views: photos before/after/fault, directions.',
    'category': 'Field Service',
    'description': '''
Field Service: Mobile
=====================

    The technician's phone view of a work order.

    Split out of elevata_fsm_mobile, which was almost entirely generic. Only
    the label "Hiss" on the equipment field was customer-specific; the rest
    applies to any field service:

        photo_before    the state before work started
        photo_after     the state when it was finished
        photo_fault     what was wrong

    Those three are the evidence a technician brings back. Without them the
    office has only the technician's word for what was found and what was
    done, and a dispute about a damaged part or a pre-existing fault has
    nothing to settle it.

    Also adds a directions action: a computed address on the order and on
    the equipment, and a button that opens Google Maps navigation. Neither
    model carries address fields of its own — the address lives on the
    partner — so it is built from there.

    Features:

        - Photo before / after / fault on the work order
        - Computed directions address on order and equipment
        - "Navigate here" button that opens Google Maps
        - Mobile list and form views sized for a phone
        - Touch-friendly buttons

    The customer-specific parts stay in elevata_fsm_mobile: the elevator
    label and the dependencies on the Elevata modules.
    ''',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_mobile',
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'depends': [
        'fieldservice_vrtl',
        'fieldservice_maintenance',
        'web_responsive',
    ],
    'data': [
        'views/fsm_order_mobile.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fieldservice_mobile/static/src/scss/mobile.scss',
        ],
    },
    'application': False,
    'installable': True,
    'auto_install': False,
}
