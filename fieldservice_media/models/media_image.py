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

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MediaImage(models.Model):
    """An image of an asset, optionally taken on a work order.

    A separate model rather than three image fields: a technician takes as
    many pictures as the job needs — the nameplate, the fault, the repair,
    the serial number — and which ones matter is different every time.

    The asset is required and the order is not. An image taken during an
    inspection belongs to the asset even if the order is later cancelled,
    and the asset form can take images without any order at all.
    """

    _name = 'fieldservice.media.image'
    _description = 'Asset and Work Order Image'
    _order = 'id desc'

    image = fields.Image(
        string='Image',
        required=True,
        attachment=True,
        max_width=1920,
        max_height=1080,
    )
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Asset',
        required=True,
        ondelete='cascade',
        index=True,
    )
    order_id = fields.Many2one(
        'fieldservice.order',
        string='Work Order',
        ondelete='set null',
        index=True,
    )
    name = fields.Char(string='Description')

    @api.model_create_multi
    def create(self, vals_list):
        """Take the asset from the order when the image is filed on one."""
        for vals in vals_list:
            if vals.get('order_id'):
                order = self.env['fieldservice.order'].browse(vals['order_id'])
                vals['equipment_id'] = order.equipment_id.id
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('order_id'):
            order = self.env['fieldservice.order'].browse(vals['order_id'])
            vals['equipment_id'] = order.equipment_id.id
        return super().write(vals)

    @api.constrains('equipment_id', 'order_id')
    def _check_order_equipment(self):
        """An image on an order must belong to the order's asset.

        Enforced rather than trusted: a picture filed against the wrong
        elevator is worse than no picture, because it looks like evidence.
        """
        for image in self.filtered('order_id'):
            if image.equipment_id != image.order_id.equipment_id:
                raise ValidationError(
                    self.env._(
                        'The image belongs to %(image_asset)s but the work '
                        'order is for %(order_asset)s.',
                        image_asset=image.equipment_id.display_name or '-',
                        order_asset=(
                            image.order_id.equipment_id.display_name or '-'
                        ),
                    )
                )


class FieldServiceOrder(models.Model):
    """Gallery on the order."""

    _inherit = 'fieldservice.order'

    image_ids = fields.One2many(
        'fieldservice.media.image',
        'order_id',
        string='Images',
    )
    image_count = fields.Integer(
        string='Images',
        compute='_compute_image_count',
    )

    @api.depends('image_ids')
    def _compute_image_count(self):
        for order in self:
            order.image_count = len(order.image_ids)

    def write(self, vals):
        """Move the images when the order's asset changes.

        Otherwise the images would stay on the old asset and the constraint
        would reject the next edit — the order and its pictures would be out
        of step with no way back.
        """
        result = super().write(vals)
        if 'equipment_id' in vals:
            for order in self:
                order.image_ids.write({'equipment_id': order.equipment_id.id})
        return result


class MaintenanceEquipment(models.Model):
    """Gallery on the asset."""

    _inherit = 'maintenance.equipment'

    image_ids = fields.One2many(
        'fieldservice.media.image',
        'equipment_id',
        string='Images',
    )
    image_count = fields.Integer(
        string='Images',
        compute='_compute_image_count',
    )

    @api.depends('image_ids')
    def _compute_image_count(self):
        for equipment in self:
            equipment.image_count = len(equipment.image_ids)
