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
class TestFieldserviceMaintenanceVrtl(TransactionCase):
    """Vertel adaptations on top of fieldservice_maintenance.

    The base module links a request to an order. This module adds the
    property on the order and the counters on the equipment — without
    touching either lifecycle.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Field Service'})
        cls.env['ir.config_parameter'].sudo().set_param(
            'fieldservice.default_project_id', cls.project.id)
        cls.property = cls.env['property.property'].create({
            'name': 'Fastighet A',
            'street': 'Storgatan 1',
            'zip': '111 22',
            'city': 'Stockholm',
        })
        cls.equipment = cls.env['maintenance.equipment'].create({
            'name': 'Elevator A',
            'is_elevator': True,
            'property_id': cls.property.id,
        })
        cls.request = cls.env['maintenance.request'].create({
            'name': 'Door does not close',
            'description': '<p>Jams on floor 3</p>',
            'equipment_id': cls.equipment.id,
        })

    def test_order_inherits_property_from_equipment(self):
        action = self.request.action_create_fieldservice_order()
        order = self.env['fieldservice.order'].browse(action['res_id'])
        self.assertEqual(order.property_id, self.property)

    def test_property_follows_equipment_change(self):
        action = self.request.action_create_fieldservice_order()
        order = self.env['fieldservice.order'].browse(action['res_id'])
        other = self.env['property.property'].create({'name': 'Fastighet B'})
        self.equipment.property_id = other
        order.invalidate_recordset(['property_id'])
        self.assertEqual(order.property_id, other)

    def test_equipment_counters(self):
        self.assertEqual(self.equipment.fieldservice_order_count, 0)
        self.request.action_create_fieldservice_order()
        self.equipment.invalidate_recordset(
            ['fieldservice_order_count', 'open_maintenance_request_count'])
        self.assertEqual(self.equipment.fieldservice_order_count, 1)
        # The request is still in its initial stage, which is not done.
        self.assertEqual(self.equipment.open_maintenance_request_count, 1)

    def test_equipment_actions_filter_on_this_asset(self):
        self.request.action_create_fieldservice_order()
        order_action = self.equipment.action_view_fieldservice_orders()
        self.assertEqual(order_action['res_model'], 'fieldservice.order')
        self.assertEqual(order_action['domain'], [('equipment_id', '=', self.equipment.id)])
        self.assertEqual(order_action['context']['default_equipment_id'], self.equipment.id)

        request_action = self.equipment.action_view_maintenance_requests()
        self.assertEqual(request_action['res_model'], 'maintenance.request')
        self.assertEqual(request_action['domain'], [('equipment_id', '=', self.equipment.id)])

    def test_cancelling_request_does_not_cancel_order(self):
        """The order keeps its own lifecycle; the link is only cleared on unlink."""
        action = self.request.action_create_fieldservice_order()
        order = self.env['fieldservice.order'].browse(action['res_id'])
        order_stage = order.stage_id

        self.request.write({'archive': True})

        self.assertTrue(order.exists())
        self.assertEqual(order.stage_id, order_stage)
