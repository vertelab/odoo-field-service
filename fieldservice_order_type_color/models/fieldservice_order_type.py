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

from odoo import fields, models


class FieldserviceOrderType(models.Model):
    """Add a colour and a service-checklist flag to the order type.

    The colour is stored as a hex string rather than an integer index: the
    set of types is customer-defined and open-ended, so a fixed palette
    would run out. The `color` widget accepts a hex value directly.

    `use_service_checklist` was carried over from Elevata's
    elevata_order_types. It lives here rather than in
    elevata_service_contract because the flag belongs to the order type,
    and the contract module reads it through
    product_tmpl_id.product_type.use_service_checklist.
    """

    _inherit = 'fieldservice.order.type'

    color = fields.Char(
        string='Color',
        default='#3498DB',
        help='Hex colour used to tell order types apart in lists.',
    )
    use_service_checklist = fields.Boolean(
        string='Generate Service Checklist',
        help='Automatically generate the service checklist on orders of '
             'this type when the equipment requires one.',
    )
