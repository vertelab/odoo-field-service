from odoo import api, fields, models


class FSMOrder(models.Model):
    _inherit = 'fieldservice.order'
    _order = 'priority desc, date_completed desc, create_date desc'

    date_completed = fields.Datetime(
        string="Completed Date",
        readonly=True,
        copy=False,
    )
    related_location_orders = fields.Many2many(
        'fieldservice.order',
        string="Related Orders",
        compute='_compute_related_orders',
    )
    active_related_orders_count = fields.Integer(
        string="Active Related Orders",
        compute='_compute_active_related_orders_count',
    )

    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' in vals:
            for order in self:
                if order.stage_id.is_closed and not order.date_completed:
                    order.date_completed = fields.Datetime.now()
        return res

    @api.depends('equipment_id')
    def _compute_related_orders(self):
        for order in self:
            if order.equipment_id:
                domain = [('equipment_id', '=', order.equipment_id.id)]
                if not isinstance(order.id, models.NewId):
                    domain.append(('id', '!=', order.id))
                order.related_location_orders = self.search(
                    domain,
                    order='date_completed desc, create_date desc',
                    limit=100,
                )
            else:
                order.related_location_orders = False

    @api.depends('related_location_orders', 'related_location_orders.stage_id')
    def _compute_active_related_orders_count(self):
        for order in self:
            order.active_related_orders_count = len(
                order.related_location_orders.filtered(lambda o: not o.is_closed)
            )

    def action_view_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Order History',
            'res_model': 'fieldservice.order',
            'view_mode': 'tree,form',
            'domain': [('equipment_id', '=', self.equipment_id.id)],
            'context': {'default_equipment_id': self.equipment_id.id},
            'target': 'current',
        }
