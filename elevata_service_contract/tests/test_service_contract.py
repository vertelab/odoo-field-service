# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestServiceContract(TransactionCase):
    """Regression tests for the 17.0 -> 18.0 port.

    Each test pins a mapping that broke during the port, so a future
    refactor cannot silently reintroduce it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Service Contract Test Customer',
            'is_company': True,
        })
        cls.equipment = cls.env['maintenance.equipment'].create({
            'name': 'TESTHISS-SC',
            'partner_id': cls.partner.id,
        })

    def _make_contract(self, **kwargs):
        return self.env['elevata.service.contract'].create(dict({
            'partner_id': self.partner.id,
            'date_start': '2026-01-01',
            'contract_years': 1,
        }, **kwargs))

    def _make_line(self, contract, **kwargs):
        return self.env['elevata.service.contract.line'].create(dict({
            'service_contract_id': contract.id,
            'equipment_id': self.equipment.id,
            'contract_type_selection': 'SERV-STD',
            'price_unit': 1000.0,
            'visits_per_year': '4',
        }, **kwargs))

    def test_date_end_computed_from_years(self):
        contract = self._make_contract(contract_years=2, date_start='2026-01-01')
        self.assertEqual(
            contract.date_end.strftime('%Y-%m-%d'), '2027-12-31',
            'date_end must be date_start + contract_years - 1 day',
        )

    def test_customer_id_falls_back_to_equipment_partner(self):
        """maintenance.equipment has no customer_id; partner_id is the owner."""
        contract = self._make_contract()
        line = self._make_line(contract)
        self.assertEqual(line.customer_id, self.partner)

    def test_confirm_requires_a_line(self):
        contract = self._make_contract()
        with self.assertRaises(Exception):
            contract.action_confirm()
        self.assertEqual(contract.state, 'draft')

    def test_confirm_generates_work_orders(self):
        """The order type is reached via product_tmpl_id, not a `type` field."""
        contract = self._make_contract()
        self._make_line(contract)
        contract.action_confirm()
        self.assertEqual(contract.state, 'confirmed')
        self.assertGreater(
            contract.fsm_order_count, 0,
            'confirming a contract with visits_per_year must create work orders',
        )
        for order in contract.fsm_order_ids:
            self.assertTrue(order.name, 'fieldservice.order.name is NOT NULL')

    def test_elevator_types_for_checklists_exist(self):
        """The 11 elevator types the checklists reference must resolve."""
        codes = ['TR', 'HY', 'MRL', 'SD', 'SDH', 'SL', 'SLH', 'SG', 'LT']
        found = self.env['maintenance.elevator.type'].search([
            ('code', 'in', codes),
        ])
        self.assertEqual(
            len(found), len(codes),
            'every elevator type referenced by the service checklists must exist',
        )

    def test_checklists_are_linked_to_elevator_types(self):
        checklists = self.env['elevata.service.checklist'].search([])
        self.assertTrue(checklists, 'service checklist data must be loaded')
        self.assertTrue(
            all(c.elevator_type_ids for c in checklists),
            'every seeded checklist must be linked to at least one elevator type',
        )
