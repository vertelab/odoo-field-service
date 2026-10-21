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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo.tests.common import TransactionCase


class TestTeamVehicle(TransactionCase):
    """Team ↔ vehicle bridge."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.team = cls.env['fieldservice.team'].create({'name': 'Crew A'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.env['fleet.vehicle.model'].create({
                'name': 'Transporter',
                'brand_id': cls.env['fleet.vehicle.model.brand'].create({
                    'name': 'VW',
                }).id,
            }).id,
            'license_plate': 'ABC123',
        })

    def test_vehicle_assigned_to_team(self):
        self.team.vehicle_ids = [(6, 0, self.vehicle.ids)]
        self.assertEqual(self.team.vehicle_count, 1)
        self.assertIn(self.team, self.vehicle.fieldservice_team_ids)

    def test_vehicle_side_creates_team_link(self):
        self.vehicle.fieldservice_team_ids = [(6, 0, self.team.ids)]
        self.assertIn(self.vehicle, self.team.vehicle_ids)

    def test_team_without_vehicle_is_valid(self):
        self.assertFalse(self.team.vehicle_ids)
        self.assertEqual(self.team.vehicle_count, 0)

    def test_vehicle_shared_by_two_teams(self):
        other = self.env['fieldservice.team'].create({'name': 'Crew B'})
        self.team.vehicle_ids = [(6, 0, self.vehicle.ids)]
        other.vehicle_ids = [(6, 0, self.vehicle.ids)]
        self.assertEqual(self.vehicle.fieldservice_team_ids, self.team | other)
