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

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFieldserviceMaintenance(TransactionCase):
    """The bridge links two independent lifecycles by reference.

    What must hold:
    - Creating an order from a request copies the description as plain text
      (maintenance.request.description is Html, fieldservice.order.description
      is Text).
    - The link is bidirectional and does not make one follow the other.
    - Calling the action twice does not create a second order.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Field Service'})
        cls.env['ir.config_parameter'].sudo().set_param(
            'fieldservice.default_project_id', cls.project.id)
        cls.partner = cls.env['res.partner'].create({'name': 'Fastighetsägare AB'})
        cls.equipment = cls.env['maintenance.equipment'].create({
            'name': 'Elevator A',
            'is_elevator': True,
            'partner_id': cls.partner.id,
        })
        cls.request = cls.env['maintenance.request'].create({
            'name': 'Door does not close',
            'description': '<p>Door <b>jams</b> on floor 3</p>',
            'equipment_id': cls.equipment.id,
        })

    def test_create_order_from_request(self):
        action = self.request.action_create_fieldservice_order()
        order = self.env['fieldservice.order'].browse(action['res_id'])

        self.assertEqual(order.maintenance_request_id, self.request)
        self.assertEqual(self.request.fieldservice_order_id, order)
        self.assertEqual(order.equipment_id, self.equipment)
        self.assertEqual(order.partner_id, self.partner)

    def test_description_is_converted_to_plain_text(self):
        action = self.request.action_create_fieldservice_order()
        order = self.env['fieldservice.order'].browse(action['res_id'])
        self.assertNotIn('<p>', order.description or '')
        self.assertNotIn('<b>', order.description or '')
        self.assertIn('jams', order.description)

    def test_action_is_idempotent(self):
        """Pressing the button twice must open the existing order, not make a new one."""
        self.request.action_create_fieldservice_order()
        first = self.request.fieldservice_order_id
        self.request.action_create_fieldservice_order()
        self.assertEqual(self.request.fieldservice_order_id, first)
        self.assertEqual(
            self.env['fieldservice.order'].search_count([
                ('maintenance_request_id', '=', self.request.id),
            ]), 1)

    def test_order_count(self):
        self.assertEqual(self.request.fieldservice_order_count, 0)
        self.request.action_create_fieldservice_order()
        self.request.invalidate_recordset(['fieldservice_order_count'])
        self.assertEqual(self.request.fieldservice_order_count, 1)

    def test_view_actions_return_act_window(self):
        self.request.action_create_fieldservice_order()
        order = self.request.fieldservice_order_id
        a1 = self.request.action_view_fieldservice_order()
        self.assertEqual(a1['res_model'], 'fieldservice.order')
        self.assertEqual(a1['res_id'], order.id)
        a2 = order.action_view_maintenance_request()
        self.assertEqual(a2['res_model'], 'maintenance.request')
        self.assertEqual(a2['res_id'], self.request.id)

    def test_lifecycles_stay_independent(self):
        """Linking must not propagate stage changes between the two records."""
        self.request.action_create_fieldservice_order()
        order = self.request.fieldservice_order_id
        request_stage = self.request.stage_id
        other_stage = self.env['fieldservice.stage'].search(
            [('id', '!=', order.stage_id.id)], limit=1)
        if other_stage:
            order.stage_id = other_stage
        self.assertEqual(self.request.stage_id, request_stage)
