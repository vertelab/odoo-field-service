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
"""Checklists on a field service work order.

A template is edited; an item is history. That split is the whole point
of the model — see ``create()`` on the item.
"""

from odoo import api, fields, models


class FieldserviceChecklist(models.Model):
    """A reusable checklist template."""

    _name = 'fieldservice.checklist'
    _description = 'Field Service Checklist Template'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    line_ids = fields.One2many(
        'fieldservice.checklist.line',
        'checklist_id',
        string='Items',
    )
    line_count = fields.Integer(
        string='Items',
        compute='_compute_line_count',
    )

    @api.depends('line_ids')
    def _compute_line_count(self):
        for checklist in self:
            checklist.line_count = len(checklist.line_ids)


class FieldserviceChecklistLine(models.Model):
    """One check item in a template."""

    _name = 'fieldservice.checklist.line'
    _description = 'Field Service Checklist Template Line'
    _order = 'sequence, id'

    checklist_id = fields.Many2one(
        'fieldservice.checklist',
        string='Checklist',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(string='Check Item', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    note = fields.Text(
        string='Note / Instruction',
        help='Shown to the technician next to the check item.',
    )


class FieldserviceChecklistItem(models.Model):
    """A filled-in check item on a work order."""

    _name = 'fieldservice.checklist.item'
    _description = 'Field Service Checklist Item (on Work Order)'
    _order = 'sequence, id'

    order_id = fields.Many2one(
        'fieldservice.order',
        string='Work Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    checklist_line_id = fields.Many2one(
        'fieldservice.checklist.line',
        string='Template Item',
        ondelete='set null',
    )
    name = fields.Char(string='Check Item', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    done = fields.Boolean(string='Done', default=False)
    note = fields.Text(string='Note')
    remark = fields.Boolean(
        string='Remark',
        default=False,
        help='Tick when the check turned up something that needs follow-up. '
             'A remark can be turned into a maintenance request.',
    )
    maintenance_request_id = fields.Many2one(
        'maintenance.request',
        string='Maintenance Request',
        ondelete='set null',
        readonly=True,
        help='Created from this remark, if any.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Copy the text from the template line.

        Two reasons. The work order view creates items with only
        ``checklist_line_id`` set, so copying here keeps the model usable
        from the UI without an onchange round-trip. And the copy is what
        freezes the historical text: editing the template later must not
        rewrite an inspection that was already performed.
        """
        for vals in vals_list:
            if not vals.get('name') and vals.get('checklist_line_id'):
                line = self.env['fieldservice.checklist.line'].browse(
                    vals['checklist_line_id'])
                vals['name'] = line.name
                vals.setdefault('sequence', line.sequence)
        return super().create(vals_list)

    def action_create_maintenance_request(self):
        """Turn a remark into a maintenance request.

        The check found something; the fix belongs in the maintenance
        system, not in the checklist. One request per item, linked back so
        the checklist shows what came of it.
        """
        self.ensure_one()
        if self.maintenance_request_id:
            return self._action_view_maintenance_request()
        request = self.env['maintenance.request'].create({
            'name': self.name,
            'equipment_id': self.order_id.equipment_id.id or False,
            'description': self.note or self.name,
            'request_date': fields.Date.context_today(self),
        })
        self.maintenance_request_id = request
        return self._action_view_maintenance_request()

    def _action_view_maintenance_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Maintenance Request'),
            'res_model': 'maintenance.request',
            'res_id': self.maintenance_request_id.id,
            'view_mode': 'form',
        }
