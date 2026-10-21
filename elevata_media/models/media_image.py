from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ElevataMediaImage(models.Model):
    _name = 'elevata.media.image'
    _description = 'Elevator and Work Order Image'
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
        string='Elevator',
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('order_id'):
                vals['equipment_id'] = self.env['fieldservice.order'].browse(
                    vals['order_id']).equipment_id.id
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('order_id'):
            vals['equipment_id'] = self.env['fieldservice.order'].browse(
                vals['order_id']).equipment_id.id
        return super().write(vals)

    @api.constrains('equipment_id', 'order_id')
    def _check_order_equipment(self):
        for image in self.filtered('order_id'):
            if image.equipment_id != image.order_id.equipment_id:
                raise ValidationError(
                    'A work order image must belong to the same elevator as '
                    'the work order.'
                )


class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'

    image_ids = fields.One2many(
        'elevata.media.image',
        'order_id',
        string='Images',
    )

    def write(self, vals):
        result = super().write(vals)
        if 'equipment_id' in vals:
            for order in self:
                order.image_ids.write({'equipment_id': order.equipment_id.id})
        return result


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    image_ids = fields.One2many(
        'elevata.media.image',
        'equipment_id',
        string='Images',
    )
