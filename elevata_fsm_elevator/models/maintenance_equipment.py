from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    elevator_number = fields.Char(
        string="Elevator Number",
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('elevator_number'):
                vals['elevator_number'] = (
                    self.env['ir.sequence'].next_by_code('elevator.number')
                )
        return super().create(vals_list)
