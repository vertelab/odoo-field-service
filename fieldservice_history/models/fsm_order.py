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


class FieldServiceOrder(models.Model):
    """History on the order: when it was finished, and what came before.

    date_end in Odoo is the planned end. The date a job was actually
    finished is different, and it is what a service history is built on —
    and what a warranty claim is measured from. It is stamped once, when
    the order enters a closed stage, and never recalculated.
    """

    _inherit = 'fieldservice.order'
    _order = 'priority desc, date_completed desc, create_date desc'

    date_completed = fields.Datetime(
        string='Completed Date',
        readonly=True,
        copy=False,
        help='Stamped when the order enters a closed stage. Not the same '
             'as the planned end.',
    )
    related_order_ids = fields.Many2many(
        'fieldservice.order',
        string='Related Orders',
        compute='_compute_related_order_ids',
        help='Other orders on the same asset, newest first.',
    )
    active_related_order_count = fields.Integer(
        string='Active Related Orders',
        compute='_compute_related_order_ids',
    )

    def write(self, vals):
        """Stamp date_completed on the transition into a closed stage.

        Only on the transition: an order already closed keeps the date it
        was closed on, even if it is reopened and closed again. Rewriting
        it would make the history say something that did not happen.
        """
        res = super().write(vals)
        if 'stage_id' in vals:
            for order in self:
                if order.stage_id.is_closed and not order.date_completed:
                    order.date_completed = fields.Datetime.now()
            # The asset's active_order_count depends on this order's stage,
            # but @api.depends across a One2many to a related model does not
            # fire when that field changes — verified: the count stayed at 2
            # with one order closed. Recompute it explicitly.
            for equipment in self.mapped('equipment_id'):
                equipment.active_order_count = len(
                    equipment.fsm_order_ids.filtered(
                        lambda o: not o.stage_id.is_closed
                    )
                )
        return res

    @api.depends('equipment_id')
    def _compute_related_order_ids(self):
        for order in self:
            if not order.equipment_id:
                order.related_order_ids = False
                order.active_related_order_count = 0
                continue
            domain = [('equipment_id', '=', order.equipment_id.id)]
            # A new record has a NewId, not an int; comparing it to an id
            # in the domain would raise. Skip the exclusion in that case.
            if not isinstance(order.id, models.NewId):
                domain.append(('id', '!=', order.id))
            related = self.search(
                domain,
                order='date_completed desc, create_date desc',
                limit=100,
            )
            order.related_order_ids = related
            order.active_related_order_count = len(
                related.filtered(lambda o: not o.stage_id.is_closed)
            )

    def action_view_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Order History'),
            'res_model': 'fieldservice.order',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.equipment_id.id)],
            'context': {'default_equipment_id': self.equipment_id.id},
            'target': 'current',
        }
