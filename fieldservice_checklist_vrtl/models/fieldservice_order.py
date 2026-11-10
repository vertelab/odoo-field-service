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
from odoo.exceptions import UserError


class FieldserviceOrder(models.Model):
    _inherit = 'fieldservice.order'

    checklist_item_ids = fields.One2many(
        'fieldservice.checklist.item',
        'order_id',
        string='Checklist',
    )
    checklist_count = fields.Integer(
        string='Checklist Items',
        compute='_compute_checklist_counts',
    )
    checklist_done_count = fields.Integer(
        string='Done',
        compute='_compute_checklist_counts',
    )

    @api.depends('checklist_item_ids', 'checklist_item_ids.done')
    def _compute_checklist_counts(self):
        for order in self:
            items = order.checklist_item_ids
            order.checklist_count = len(items)
            order.checklist_done_count = len(items.filtered('done'))

    def action_generate_checklist(self):
        """Fill the order from every active template.

        An order that already has items is left alone. Regenerating would
        overwrite what the technician has already ticked, and an
        inspection that was performed is not something to recalculate.
        """
        self.ensure_one()
        if self.checklist_item_ids:
            raise UserError(self.env._(
                'This order already has a checklist. Remove the existing '
                'items first if it should be regenerated.'))
        items = []
        for checklist in self.env['fieldservice.checklist'].search([]):
            for line in checklist.line_ids:
                items.append((0, 0, {
                    'checklist_line_id': line.id,
                    'name': line.name,
                    'sequence': line.sequence,
                }))
        if items:
            self.write({'checklist_item_ids': items})
        return True
