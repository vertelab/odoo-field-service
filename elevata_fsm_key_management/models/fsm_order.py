from odoo import api, fields, models


class FSMOrder(models.Model):
    _inherit = 'fieldservice.order'

    key_access_info = fields.Text(string="Key Access Info")
    key_ids = fields.Many2many(
        'elevata.key', string="Keys",
        compute='_compute_key_info', store=True,
    )
    key_codes = fields.Text(
        string="Key Codes", compute='_compute_key_info', store=True,
    )
    key_position_addresses = fields.Text(
        string="Key Position Addresses", compute='_compute_key_info', store=True,
    )
    key_position_codes = fields.Text(
        string="Key Position Codes", compute='_compute_key_info', store=True,
    )
    key_position_map_url = fields.Char(
        string="Key Position Map URL",
        related='equipment_id.key_position_map_url',
        readonly=True,
    )
    key_notes = fields.Text(
        string="Key Notes",
        related='equipment_id.key_notes',
        readonly=True,
    )

    @api.depends(
        'equipment_id', 'equipment_id.key_ids', 'equipment_id.key_ids.code',
        'equipment_id.key_ids.notes', 'equipment_id.key_ids.position_id',
        'equipment_id.key_ids.position_id.street',
        'equipment_id.key_ids.position_id.city',
        'equipment_id.key_ids.position_id.zip',
        'equipment_id.key_ids.position_id.code',
    )
    def _compute_key_info(self):
        for order in self:
            if order.equipment_id and order.equipment_id.key_ids:
                order.key_ids = order.equipment_id.key_ids

                info_parts = []
                for key in order.equipment_id.key_ids:
                    if key.code:
                        info_parts.append(key.code)
                    if key.notes:
                        info_parts.append(key.notes)
                order.key_codes = '\n'.join(info_parts) if info_parts else ''

                positions = order.equipment_id.key_ids.mapped('position_id').filtered('street')
                addresses = []
                for pos in positions:
                    parts = [pos.street]
                    if pos.zip and pos.city:
                        parts.append("%s %s" % (pos.zip, pos.city))
                    addresses.append(', '.join(parts))
                order.key_position_addresses = '\n'.join(addresses) if addresses else ''

                pos_codes = [
                    c for c in order.equipment_id.key_ids.mapped('position_id.code') if c
                ]
                order.key_position_codes = '\n'.join(pos_codes) if pos_codes else ''
            else:
                order.key_ids = False
                order.key_codes = False
                order.key_position_addresses = False
                order.key_position_codes = False
