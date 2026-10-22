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

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFieldserviceChecklist(TransactionCase):
    """The contract this module promises.

    The interesting parts are the two that are easy to get wrong:
    generating twice must not overwrite, and editing a template must not
    rewrite history.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The database ships with Elevata's 11 elevator templates. Archive
        # them so this test owns the whole table and the counts mean what
        # they say.
        cls.env['fieldservice.checklist'].search([]).active = False
        cls.checklist = cls.env['fieldservice.checklist'].create({
            'name': 'Quarterly inspection',
            'line_ids': [
                (0, 0, {'name': 'Check door interlock', 'sequence': 10}),
                (0, 0, {'name': 'Check alarm button', 'sequence': 20}),
                (0, 0, {'name': 'Check emergency light', 'sequence': 30}),
            ],
        })
        cls.order = cls.env['fieldservice.order'].create({
            'name': 'FSM/TEST/001',
            # severity_level is required by fieldservice_sla and drives SLA
            # selection — an order cannot exist without it.
            'severity_level': 'low',
        })

    def test_line_count(self):
        """The template counts its own lines."""
        self.assertEqual(self.checklist.line_count, 3)

    def test_generate_copies_lines(self):
        """Generating fills the order from the template."""
        self.order.action_generate_checklist()
        self.assertEqual(self.order.checklist_count, 3)
        self.assertEqual(
            sorted(self.order.checklist_item_ids.mapped('name')),
            ['Check alarm button', 'Check door interlock',
             'Check emergency light'],
        )

    def test_generate_sets_counts(self):
        """The done counter starts at zero and follows the ticks."""
        self.order.action_generate_checklist()
        self.assertEqual(self.order.checklist_done_count, 0)
        self.order.checklist_item_ids[0].done = True
        self.assertEqual(self.order.checklist_done_count, 1)

    def test_generate_twice_is_refused(self):
        """An order that already has items is left alone.

        Regenerating would overwrite what the technician has already
        ticked, and a performed inspection is not something to
        recalculate.
        """
        self.order.action_generate_checklist()
        with self.assertRaises(UserError):
            self.order.action_generate_checklist()
        self.assertEqual(self.order.checklist_count, 3)

    def test_item_freezes_name_at_creation(self):
        """Editing the template does not rewrite a performed inspection."""
        self.order.action_generate_checklist()
        item = self.order.checklist_item_ids.filtered(
            lambda i: i.name == 'Check door interlock')
        self.assertTrue(item, 'expected the item to exist')
        line = item.checklist_line_id
        line.name = 'Check door interlock (revised)'
        self.assertEqual(item.name, 'Check door interlock')
        self.assertEqual(line.name, 'Check door interlock (revised)')

    def test_item_takes_name_from_line(self):
        """Creating with only the line set fills name and sequence."""
        line = self.checklist.line_ids[0]
        item = self.env['fieldservice.checklist.item'].create({
            'order_id': self.order.id,
            'checklist_line_id': line.id,
        })
        self.assertEqual(item.name, line.name)
        self.assertEqual(item.sequence, line.sequence)

    def test_item_sequence_follows_template(self):
        """The order of the template survives into the order."""
        self.order.action_generate_checklist()
        sequences = self.order.checklist_item_ids.sorted('sequence').mapped(
            'name')
        self.assertEqual(sequences[0], 'Check door interlock')
        self.assertEqual(sequences[-1], 'Check emergency light')

    def test_order_unlink_cascades(self):
        """Deleting the order takes its checklist with it."""
        self.order.action_generate_checklist()
        items = self.order.checklist_item_ids
        self.order.unlink()
        self.assertFalse(items.exists())
