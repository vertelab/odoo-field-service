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
    'name': 'Field Service: Media',
    'version': '18.0.1.0.0',
    # Version ledger: 18.0 = Odoo version. 1 = Major. Non regressionable code.
    # 0 = Minor. 1 = Bug fixes
    'summary': 'Image gallery per asset and per work order.',
    'category': 'Field Service',
    'description': '''
Field Service: Media
====================

    An image gallery on the asset and on the work order.

    Split out of elevata_media, which was entirely generic: an image belongs
    to an asset, optionally to the work order it was taken on. Nothing in
    the model was elevator-specific.

    Why a separate model and not three image fields: a technician takes as
    many pictures as the job needs — the nameplate, the fault, the repair,
    the serial number. Three fixed fields force a choice about which three
    matter, and that choice is different every time.

    fieldservice_mobile carries photo_before, photo_after and photo_fault:
    the three the office asks for on every job. This module is the gallery
    for everything else.

    The asset is required, the order is not. An image taken during an
    inspection belongs to the asset even if the order is later cancelled,
    and an image can be added from the asset form without an order at all.

    An image on an order must belong to the same asset as the order. That
    is enforced rather than trusted: a picture filed against the wrong
    elevator is worse than no picture.

    Features:

        - Image gallery on the asset and on the work order
        - Order images inherit the order's asset
        - Changing an order's asset moves its images with it
        - Constraint: order images must match the order's asset
    ''',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_media',
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
        'views/media_image_views.xml',
        'views/fsm_order_views.xml',
        'views/maintenance_equipment_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
