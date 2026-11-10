from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    fieldservice_order_ids = fields.One2many(
        'fieldservice.order', 'equipment_id',
        string='Field Service Orders',
    )
    fieldservice_order_count = fields.Integer(
        compute='_compute_fieldservice_order_count',
        string='Field Service Orders',
    )
    open_maintenance_request_count = fields.Integer(
        compute='_compute_open_maintenance_request_count',
        string='Open Maintenance Requests',
    )

    @api.depends('fieldservice_order_ids')
    def _compute_fieldservice_order_count(self):
        for equipment in self:
            equipment.fieldservice_order_count = len(equipment.fieldservice_order_ids)

    @api.depends('maintenance_ids')
    def _compute_open_maintenance_request_count(self):
        # maintenance.equipment.maintenance_ids is the core One2many back to
        # maintenance.request. A request is open until it is repaired or
        # scrapped; stage_id is what carries that, so we filter on the
        # stage sequence rather than on a fixed name.
        for equipment in self:
            equipment.open_maintenance_request_count = len(
                equipment.maintenance_ids.filtered(
                    lambda r: r.stage_id.done is False
                )
            )

    def action_view_fieldservice_orders(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'fieldservice_vrtl.action_fieldservice_order'
        )
        action['domain'] = [('equipment_id', '=', self.id)]
        action['context'] = {
            'default_equipment_id': self.id,
            'default_company_id': self.company_id.id,
        }
        return action

    def action_view_maintenance_requests(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'maintenance.hr_equipment_request_action'
        )
        action['domain'] = [('equipment_id', '=', self.id)]
        action['context'] = {'default_equipment_id': self.id}
        return action
