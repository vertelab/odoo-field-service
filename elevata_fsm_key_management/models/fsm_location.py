from odoo import api, fields, models
from werkzeug.urls import url_encode


class FSMLocation(models.Model):
    _inherit = 'maintenance.equipment'

    key_access_info = fields.Text(string="Key Access Info")
    key_ids = fields.Many2many('elevata.key', string="Keys")
    key_codes = fields.Char(
        string="Key Codes", compute='_compute_key_info', store=True,
    )
    key_position_addresses = fields.Text(
        string="Key Position Addresses", compute='_compute_key_info', store=True,
    )
    key_position_codes = fields.Text(
        string="Key Position Codes", compute='_compute_key_info', store=True,
    )
    key_notes = fields.Text(
        string="Key Notes", compute='_compute_key_info', store=True,
    )
    key_position_map_url = fields.Char(
        string="Map URL", compute='_compute_key_position_map_url',
    )

    @api.depends(
        'key_ids', 'key_ids.code', 'key_ids.notes',
        'key_ids.position_id', 'key_ids.position_id.street',
        'key_ids.position_id.city', 'key_ids.position_id.zip',
        'key_ids.position_id.code',
    )
    def _compute_key_info(self):
        for location in self:
            codes = [c for c in location.key_ids.mapped('code') if c]
            location.key_codes = ', '.join(codes) if codes else ''

            positions = location.key_ids.mapped('position_id').filtered('street')
            addresses = []
            for pos in positions:
                parts = [pos.street]
                if pos.zip and pos.city:
                    parts.append("%s %s" % (pos.zip, pos.city))
                elif pos.city:
                    parts.append(pos.city)
                addresses.append(', '.join(parts))
            location.key_position_addresses = '\n'.join(addresses) if addresses else ''

            pos_codes = [
                c for c in location.key_ids.mapped('position_id.code') if c
            ]
            location.key_position_codes = ', '.join(pos_codes) if pos_codes else ''

            notes = [n for n in location.key_ids.mapped('notes') if n]
            location.key_notes = '\n'.join(notes) if notes else ''

    @api.depends('key_position_addresses')
    def _compute_key_position_map_url(self):
        for rec in self:
            if rec.key_position_addresses:
                address = rec.key_position_addresses.split('\n')[0]
                params = {'api': '1', 'destination': address}
                rec.key_position_map_url = (
                    "https://www.google.com/maps/dir/?%s" % url_encode(params)
                )
            else:
                rec.key_position_map_url = False

    def open_google_maps(self):
        if self.key_position_addresses:
            address = self.key_position_addresses.split('\n')[0]
            params = {'api': '1', 'destination': address}
            return {
                'type': 'ir.actions.act_url',
                'url': "https://www.google.com/maps/dir/?%s" % url_encode(params),
                'target': 'new',
            }
