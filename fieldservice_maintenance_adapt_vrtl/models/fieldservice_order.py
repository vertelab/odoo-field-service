from odoo import api, fields, models


class FieldserviceOrder(models.Model):
    _inherit = 'fieldservice.order'

    property_id = fields.Many2one(
        'property.property',
        compute='_compute_property_id',
        store=True,
        readonly=False,
        string='Property',
        help="Inherited from the equipment. A technician is dispatched to a "
             "property, so the dispatch list can be grouped by it.",
    )

    @api.depends('equipment_id.property_id')
    def _compute_property_id(self):
        for order in self:
            order.property_id = order.equipment_id.property_id
