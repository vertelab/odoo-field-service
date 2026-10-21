# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOffer(TransactionCase):
    """Regression tests for the 17.0 -> 18.0 port."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Offer Test Customer',
            'is_company': True,
        })

    def _make_offer(self):
        offer = self.env['elevata.offer'].create({'partner_id': self.partner.id})
        self.env['elevata.offer.line'].create({
            'offer_id': offer.id,
            'name': 'Test line',
            'quantity': 1,
            'price_unit': 5000.0,
        })
        return offer

    def test_sequence_and_draft_state(self):
        offer = self._make_offer()
        self.assertTrue(offer.name.startswith('OFF/'))
        self.assertEqual(offer.state, 'draft')

    def test_line_amounts_include_tax(self):
        offer = self._make_offer()
        self.assertAlmostEqual(offer.amount_untaxed, 5000.0, places=2)
        self.assertGreater(
            offer.amount_total, offer.amount_untaxed,
            'offer total must include tax',
        )

    def test_lifecycle(self):
        offer = self._make_offer()
        offer.action_send()
        self.assertEqual(offer.state, 'sent')
        offer.action_negotiation()
        self.assertEqual(offer.state, 'negotiation')
        offer.action_won()
        self.assertEqual(offer.state, 'won')

    def test_service_contract_link_exists(self):
        """elevata_offer depends on elevata_service_contract; the link is
        the reason the two must be ported together."""
        offer = self._make_offer()
        self.assertIn('service_contract_id', offer._fields)
        self.assertIn('service_contract_count', offer._fields)

    def test_templates_and_pricelist_loaded(self):
        self.assertTrue(
            self.env['elevata.offer.template'].search_count([]),
            'offer template data must be loaded',
        )
        self.assertTrue(
            self.env['elevata.price.rule'].search_count([]),
            'pricelist data must be loaded',
        )
