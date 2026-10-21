# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReporting(TransactionCase):
    """KPI computes on maintenance.equipment (the Odoo 18 elevator model)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.equipment = cls.env['maintenance.equipment'].create({
            'name': 'KPI-HISS-1',
            'is_elevator': True,
        })

    def _make_order(self, name):
        return self.env['fieldservice.order'].create({
            'name': name,
            'equipment_id': self.equipment.id,
        })

    def test_kpi_fields_exist(self):
        for fname in ('repeat_order_count', 'repeat_problem_warning',
                      'has_active_contract', 'inspection_soon',
                      'warranty_order_count'):
            self.assertIn(fname, self.env['maintenance.equipment']._fields)

    def test_repeat_order_count_counts_recent_orders(self):
        self.assertEqual(self.equipment.repeat_order_count, 0)
        self._make_order('KPI-ORDER-1')
        self._make_order('KPI-ORDER-2')
        self.equipment.invalidate_recordset()
        self.assertEqual(self.equipment.repeat_order_count, 2)

    def test_repeat_problem_warning_threshold(self):
        for i in range(3):
            self._make_order('KPI-ORDER-W%d' % i)
        self.equipment.invalidate_recordset()
        self.assertEqual(self.equipment.repeat_order_count, 3)
        self.assertTrue(self.equipment.repeat_problem_warning)

    def test_old_orders_not_counted(self):
        """Orders older than six months must fall outside the window."""
        order = self._make_order('KPI-ORDER-OLD')
        old = fields.Datetime.now() - timedelta(days=200)
        self.env.cr.execute(
            'UPDATE fieldservice_order SET create_date = %s WHERE id = %s',
            (old, order.id),
        )
        order.invalidate_recordset()
        self.equipment.invalidate_recordset()
        self.assertEqual(self.equipment.repeat_order_count, 0)

    def test_warranty_order_count(self):
        self.assertEqual(self.equipment.warranty_order_count, 0)

    def test_action_view_fsm_orders_reporting(self):
        self._make_order('KPI-ORDER-A')
        action = self.equipment.action_view_fsm_orders_reporting()
        self.assertEqual(action['res_model'], 'fieldservice.order')
        self.assertEqual(action['view_mode'], 'list,form')
        self.assertEqual(action['domain'], [('equipment_id', '=', self.equipment.id)])

    def test_reporting_views_installed(self):
        for xid in ('view_fsm_location_tree_reporting',
                    'view_fsm_location_search_reporting'):
            view = self.env.ref('elevata_reporting.%s' % xid, raise_if_not_found=False)
            self.assertTrue(view, 'Missing view %s' % xid)
            self.assertTrue(view.get_combined_arch())

    def test_menu_root_has_children(self):
        root = self.env.ref('elevata_reporting.menu_elevata_reporting_root')
        children = self.env['ir.ui.menu'].sudo().search([('parent_id', '=', root.id)])
        self.assertEqual(len(children), 3)
