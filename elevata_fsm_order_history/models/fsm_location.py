from odoo import api, fields, models


class FSMLocation(models.Model):
    _inherit = 'maintenance.equipment'

    fsm_order_ids = fields.One2many(
        'fieldservice.order', 'equipment_id',
        string="Order History",
    )

    active_order_count = fields.Integer(
        string="Active Orders",
        compute='_compute_active_order_count',
    )

    def _compute_active_order_count(self):
        for location in self:
            location.active_order_count = self.env['fieldservice.order'].search_count([
                ('equipment_id', '=', location.id),
                ('is_closed', '=', False),
            ])

    def action_view_orders(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'fieldservice.action_fsm_operation_order'
        )
        action.update({
            'name': 'Order History',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
            'view_mode': 'tree,form',
        })
        return action
