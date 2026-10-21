from urllib.parse import quote_plus

from odoo import fields, models


def _full_address(record):
    """Return the record's address as a single line.

    fieldservice.order and maintenance.equipment hold no address fields of
    their own, so both models expose a computed directions_address.
    """
    if 'directions_address' in record._fields:
        return record.directions_address or ''
    parts = [
        getattr(record, 'street', ''),
        getattr(record, 'street2', ''),
        ' '.join(p for p in (getattr(record, 'zip', ''), getattr(record, 'city', '')) if p),
    ]
    return ', '.join(p for p in parts if p)


def _directions_action(record):
    address = _full_address(record)
    if not address:
        return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'title': 'Ingen adress',
                           'message': 'Posten saknar adressuppgifter.',
                           'type': 'warning', 'sticky': False}}
    return {
        'type': 'ir.actions.act_url',
        'url': 'https://www.google.com/maps/dir/?api=1&destination=' + quote_plus(address),
        'target': 'new',
    }


class FSMOrder(models.Model):
    _inherit = 'fieldservice.order'

    photo_before = fields.Image(
        string='Foto före',
        max_width=1920,
        max_height=1080,
        help='Foto taget innan arbetet påbörjades.',
    )
    photo_after = fields.Image(
        string='Foto efter',
        max_width=1920,
        max_height=1080,
        help='Foto taget efter att arbetet slutförts.',
    )
    photo_fault = fields.Image(
        string='Foto på fel',
        max_width=1920,
        max_height=1080,
        help='Foto på eventuellt fel eller skada.',
    )

    directions_address = fields.Char(
        string='Adress',
        compute='_compute_directions_address',
        help='Fullständig adress. Klickbar — öppnar Google Maps vägbeskrivning.',
    )

    def _compute_directions_address(self):
        # fieldservice.order has no address fields of its own: the address
        # lives on the reporter/stakeholder partner. Build it from there.
        for rec in self:
            partner = rec.reporter_id if 'reporter_id' in rec._fields else None
            if not partner and 'partner_id' in rec._fields:
                partner = rec.partner_id
            if not partner:
                rec.directions_address = ''
                continue
            parts = [
                partner.street,
                partner.street2,
                ' '.join(p for p in (partner.zip, partner.city) if p),
            ]
            rec.directions_address = ', '.join(p for p in parts if p)

    def action_open_directions(self):
        self.ensure_one()
        return _directions_action(self)


class FSMLocation(models.Model):
    _inherit = 'maintenance.equipment'

    directions_address = fields.Char(
        string='Adress',
        compute='_compute_directions_address',
        help='Fullständig adress. Klickbar — öppnar Google Maps vägbeskrivning.',
    )

    def _compute_directions_address(self):
        # maintenance.equipment carries no address either; the customer
        # address is on partner_id.
        for rec in self:
            partner = rec.partner_id
            if not partner:
                rec.directions_address = ''
                continue
            parts = [
                partner.street,
                partner.street2,
                ' '.join(p for p in (partner.zip, partner.city) if p),
            ]
            rec.directions_address = ', '.join(p for p in parts if p)

    def action_open_directions(self):
        self.ensure_one()
        return _directions_action(self)
