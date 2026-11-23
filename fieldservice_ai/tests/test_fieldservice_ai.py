# -*- coding: utf-8 -*-
"""Tester för fieldservice_ai — kontext, resolver och verktyg."""

from odoo.tests.common import TransactionCase


class TestFieldServiceContext(TransactionCase):
    """Sessionens domänkontext."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'FSM-kund AB'})
        cls.location = cls.env['fsm.location'].create({
            'name': 'Testplats',
            'owner_id': cls.partner.id,
        })
        cls.order = cls.env['fsm.order'].create({
            'name': 'Testorder',
            'location_id': cls.location.id,
        })

    def _new_session(self):
        return self.env['ai.coworker.session'].create({
            'init_type': 'web_ui',
        })

    def test_capture_context_sets_order_and_location(self):
        """_capture_context sätter order, plats och härleder kund."""
        session = self._new_session()
        session._capture_context(fsm_order=self.order)
        self.assertEqual(session.fsm_order_id, self.order)
        self.assertEqual(session.fsm_location_id, self.location)
        self.assertEqual(session.partner_id, self.partner)

    def test_capture_context_keeps_existing_partner(self):
        """En satt partner skrivs inte över."""
        other = self.env['res.partner'].create({'name': 'Annan kund'})
        session = self._new_session()
        session.partner_id = other
        session._capture_context(fsm_order=self.order)
        self.assertEqual(session.fsm_order_id, self.order)
        self.assertEqual(session.partner_id, other)

    def test_resolver_sets_partner_from_location(self):
        """fieldservice_partner härleder kund via orderns plats."""
        from odoo.addons.fieldservice_ai.models.ai_coworker_session import (
            _fieldservice_partner_strategy)
        session = self._new_session()
        session.fsm_order_id = self.order
        session.partner_id = False
        _fieldservice_partner_strategy(session)
        self.assertEqual(session.partner_id, self.partner)

    def test_resolver_does_not_guess(self):
        """Utan order sätts ingen partner."""
        from odoo.addons.fieldservice_ai.models.ai_coworker_session import (
            _fieldservice_partner_strategy)
        session = self._new_session()
        session.partner_id = False
        _fieldservice_partner_strategy(session)
        self.assertFalse(session.partner_id)

    def test_auto_capture_from_order_id(self):
        """'arbetsorder <id>' fångas till order."""
        session = self._new_session()
        session._session_auto_capture(
            'Titta på arbetsorder %s tack' % self.order.id)
        self.assertEqual(session.fsm_order_id, self.order)

    def test_auto_capture_does_not_overwrite(self):
        """Ett satt order skrivs inte över."""
        other = self.env['fsm.order'].create({
            'name': 'Annan order',
            'location_id': self.location.id,
        })
        session = self._new_session()
        session.fsm_order_id = other
        session._session_auto_capture(
            'Titta på arbetsorder %s' % self.order.id)
        self.assertEqual(session.fsm_order_id, other)


class TestFieldServiceTools(TransactionCase):
    """Verktygens affärslogik (fieldservice.ai)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Verktygskund'})
        cls.location = cls.env['fsm.location'].create({
            'name': 'Verktygsplats',
            'owner_id': cls.partner.id,
        })
        # Använd en befintlig etapp — fsm.stage kräver unik
        # (stage_type, sequence), så vi skapar inte en ny.
        cls.stage = cls.env['fsm.stage'].search(
            [('stage_type', '=', 'order')], limit=1)
        if not cls.stage:
            cls.stage = cls.env['fsm.stage'].create({
                'name': 'Completed',
                'stage_type': 'order',
                'sequence': 99,
            })
        cls.order = cls.env['fsm.order'].create({
            'name': 'Verktygsorder',
            'location_id': cls.location.id,
        })

    def test_order_get_returns_fields(self):
        """order_get returnerar namn, plats och kund."""
        res = self.env['fieldservice.ai'].order_get(self.order.id)
        self.assertEqual(res['id'], self.order.id)
        self.assertEqual(res['partner_name'], 'Verktygskund')
        self.assertEqual(res['location_id'], self.location.id)

    def test_order_get_missing(self):
        """Saknad order ger ett tydligt fel."""
        res = self.env['fieldservice.ai'].order_get(999999)
        self.assertIn('error', res)

    def test_order_set_stage(self):
        """order_set_stage flyttar ordern."""
        ok, msg = self.env['fieldservice.ai'].order_set_stage(
            self.order.id, self.stage.name)
        self.assertTrue(ok, msg)
        self.assertEqual(self.order.stage_id, self.stage)

    def test_order_set_stage_unknown(self):
        """Okänd etapp ger ett åtgärdbart fel."""
        ok, msg = self.env['fieldservice.ai'].order_set_stage(
            self.order.id, 'Finns Inte')
        self.assertFalse(ok)
        self.assertIn('No stage named', msg)

    def test_order_update_fields(self):
        """order_update_fields ändrar prioritet."""
        ok, msg = self.env['fieldservice.ai'].order_update_fields(
            self.order.id, priority='3')
        self.assertTrue(ok, msg)
        self.assertEqual(self.order.priority, '3')

    def test_order_update_fields_nothing(self):
        """Inga fält angivna ger ett tydligt fel."""
        ok, msg = self.env['fieldservice.ai'].order_update_fields(
            self.order.id)
        self.assertFalse(ok)
        self.assertIn('Nothing to update', msg)

    def test_order_add_message(self):
        """order_add_message postar i chatter."""
        before = len(self.order.message_ids)
        ok, msg = self.env['fieldservice.ai'].order_add_message(
            self.order.id, 'Testmeddelande')
        self.assertTrue(ok, msg)
        self.assertGreater(len(self.order.message_ids), before)

    def test_order_add_message_empty(self):
        """Tomt meddelande vägras."""
        ok, msg = self.env['fieldservice.ai'].order_add_message(
            self.order.id, '')
        self.assertFalse(ok)
        self.assertIn('Missing message body', msg)
