# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFsmMobile(TransactionCase):
    """Regression tests for the mobile technician views.

    The port replaced fsm.order/fsm.location with fieldservice.order and
    maintenance.equipment, and dropped the non-existent image_ids field in
    favour of the module's own photo_* fields.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Mobilkund AB',
            'is_company': True,
            'street': 'Storgatan 1',
            'street2': '2 tr',
            'zip': '111 22',
            'city': 'Stockholm',
        })
        cls.equipment = cls.env['maintenance.equipment'].create({
            'name': 'MOBILHISS-1',
            'partner_id': cls.partner.id,
        })
        cls.order = cls.env['fieldservice.order'].create({
            'name': 'MOBIL-ORDER-1',
            'equipment_id': cls.equipment.id,
        })

    def test_photo_fields_exist(self):
        for fname in ('photo_before', 'photo_after', 'photo_fault'):
            self.assertIn(fname, self.env['fieldservice.order']._fields)

    def test_directions_address_on_order(self):
        """The computed address must not raise on a bare order."""
        self.assertEqual(self.order.directions_address, '')

    def test_directions_address_on_equipment(self):
        """maintenance.equipment has no street fields, so the address is empty.

        It falls back to the partner address; with no street on the
        equipment the compute must still return a string.
        """
        self.assertIsInstance(self.equipment.directions_address, str)

    def test_action_open_directions_without_address(self):
        """Without an address the action must be a warning notification."""
        action = self.order.action_open_directions()
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'display_notification')

    def test_mobile_views_installed(self):
        expected = [
            'view_fsm_order_mobile_list',
            'view_fsm_order_mobile_form',
            'view_fsm_location_form_mobile_nav',
        ]
        for xid in expected:
            view = self.env.ref('elevata_fsm_mobile.%s' % xid, raise_if_not_found=False)
            self.assertTrue(view, 'Missing view %s' % xid)
            self.assertTrue(view.get_combined_arch())

    def test_root_menu_has_children(self):
        root = self.env.ref('elevata_fsm_mobile.menu_mobile_root')
        tech = self.env.ref('fieldservice_vrtl.fieldservice_group_technician')
        self.env.user.groups_id = [(4, tech.id)]
        children = self.env['ir.ui.menu'].search([('parent_id', '=', root.id)])
        self.assertEqual(len(children), 5)
