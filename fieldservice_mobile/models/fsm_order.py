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

from urllib.parse import quote_plus

from odoo import fields, models


def _full_address(record):
    """Return the record's address as a single line.

    Neither fieldservice.order nor maintenance.equipment carries address
    fields of its own — the address lives on the partner. Both models
    expose a computed directions_address instead, and this helper prefers
    it when present so a subclass can override the source.
    """
    if 'directions_address' in record._fields:
        return record.directions_address or ''
    parts = [
        getattr(record, 'street', ''),
        getattr(record, 'street2', ''),
        ' '.join(
            p for p in (getattr(record, 'zip', ''), getattr(record, 'city', ''))
            if p
        ),
    ]
    return ', '.join(p for p in parts if p)


def _directions_action(record):
    """Open Google Maps navigation to the record's address.

    Returns a notification rather than raising when the address is missing:
    the technician is standing on a phone, and a traceback is not a useful
    answer to "why can't I navigate?".
    """
    address = _full_address(record)
    if not address:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'No address',
                'message': 'This record has no address to navigate to.',
                'type': 'warning',
                'sticky': False,
            },
        }
    return {
        'type': 'ir.actions.act_url',
        'url': 'https://www.google.com/maps/dir/?api=1&destination='
               + quote_plus(address),
        'target': 'new',
    }


class FieldServiceOrder(models.Model):
    """Photos and directions on the work order.

    The three photos are the evidence a technician brings back: what it
    looked like before, what was wrong, and what it looked like after.
    Without them the office has only the technician's word, and a dispute
    about a damaged part or a pre-existing fault has nothing to settle it.
    """

    _inherit = 'fieldservice.order'

    photo_before = fields.Image(
        string='Photo Before',
        max_width=1920,
        max_height=1080,
        help='Taken before work started.',
    )
    photo_after = fields.Image(
        string='Photo After',
        max_width=1920,
        max_height=1080,
        help='Taken when the work was finished.',
    )
    photo_fault = fields.Image(
        string='Photo of Fault',
        max_width=1920,
        max_height=1080,
        help='Taken of the fault or damage found.',
    )
    directions_address = fields.Char(
        string='Address',
        compute='_compute_directions_address',
        help='Full address. Opens Google Maps directions.',
    )

    def _compute_directions_address(self):
        for order in self:
            partner = (
                order.reporter_id if 'reporter_id' in order._fields else None
            )
            if not partner and 'partner_id' in order._fields:
                partner = order.partner_id
            if not partner:
                order.directions_address = ''
                continue
            parts = [
                partner.street,
                partner.street2,
                ' '.join(p for p in (partner.zip, partner.city) if p),
            ]
            order.directions_address = ', '.join(p for p in parts if p)

    def action_open_directions(self):
        self.ensure_one()
        return _directions_action(self)


class MaintenanceEquipment(models.Model):
    """Directions from the equipment form.

    An equipment record carries no address either; the customer address is
    on partner_id. Same helper, same button.
    """

    _inherit = 'maintenance.equipment'

    directions_address = fields.Char(
        string='Address',
        compute='_compute_directions_address',
        help='Full address. Opens Google Maps directions.',
    )

    def _compute_directions_address(self):
        for equipment in self:
            partner = equipment.partner_id
            if not partner:
                equipment.directions_address = ''
                continue
            parts = [
                partner.street,
                partner.street2,
                ' '.join(p for p in (partner.zip, partner.city) if p),
            ]
            equipment.directions_address = ', '.join(p for p in parts if p)

    def action_open_directions(self):
        self.ensure_one()
        return _directions_action(self)
