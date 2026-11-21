# -*- coding: utf-8 -*-
"""Kostnadskontext på ai.coworker.session — domänfält för fältservice.

`fieldservice_ai`: `fsm_order_id` och `fsm_location_id` läggs via arv i
bryggan (core förblir domän-rent).

Registrerar resolver-strategin "fieldservice_partner": kunden nås via
`order.location_id.partner_id` — `fsm.order` har ingen egen `partner_id`,
eftersom `fsm.location` ärver `res.partner` (`_inherits`).

Mönstret är project_ai:s (`project_ai/models/ai_coworker_session.py`).
"""

import logging
import re

from odoo import fields, models

_logger = logging.getLogger(__name__)


def _fieldservice_partner_strategy(session):
    """Resolver: hitta res.partner via order → location → owner.

    KUNDEN är `location.owner_id`, inte `location.partner_id` — fsm.location
    ÄRVER res.partner (`_inherits`), så `partner_id` pekar på platsens egen
    post (som heter platsens namn), inte på kunden. Verifierat mot
    fsm_location.py:27-31 (2026-11-21).

    Ingen gissning: saknas order eller location sätts ingen partner.
    """
    order = session.fsm_order_id
    if order and order.location_id and order.location_id.owner_id:
        session.partner_id = order.location_id.owner_id.id


try:
    from odoo.addons.ai_agent_core.models.ai_session import (
        register_cost_context_strategy)
    register_cost_context_strategy(
        'fieldservice_partner', _fieldservice_partner_strategy)
except Exception as e:  # pragma: no cover — modulordning
    _logger.warning(
        'kunde inte registrera fieldservice_partner-strategi: %s', e)


class AICoworkerSessionFieldService(models.Model):
    _inherit = 'ai.coworker.session'

    fsm_order_id = fields.Many2one(
        'fsm.order', string='Arbetsorder', index=True,
        ondelete='set null',
        help='Arbetsorder (fsm.order) som sessionen arbetar med. '
             'Kund härleds via orderns plats.')
    fsm_location_id = fields.Many2one(
        'fsm.location', string='Plats', index=True,
        ondelete='set null',
        help='Plats (fsm.location) som sessionen arbetar med. '
             'Sätts via arbetsordern.')

    def _capture_context(self, fsm_order=None, location=None, partner=None,
                         object_ref=None, **kwargs):
        """En enda skrivpunkt för fältservice-kostnadskontext.

        Härledning: fsm_order_id ← fsm_order; fsm_location_id ←
        order.location_id; partner_id ← location.partner_id.

        Befintliga värden behålls om inget nytt ges ("senast arbetad
        kontext vinner"). En redan satt partner skrivs inte över.

        Anropar super() så övriga bryggor samlas i MRO-kedjan.
        """
        self.ensure_one()
        vals = {}
        if fsm_order:
            o = fsm_order if isinstance(fsm_order, models.BaseModel) else \
                self.env['fsm.order'].browse(int(fsm_order))
            if o:
                vals['fsm_order_id'] = o.id
                if o.location_id:
                    vals['fsm_location_id'] = o.location_id.id
                    # Kunden är owner_id — se resolver-docstringen.
                    if o.location_id.owner_id and not self.partner_id:
                        vals['partner_id'] = o.location_id.owner_id.id
        if location:
            loc = location if isinstance(location, models.BaseModel) else \
                self.env['fsm.location'].browse(int(location))
            if loc:
                vals['fsm_location_id'] = loc.id
                if loc.owner_id and not self.partner_id:
                    vals['partner_id'] = loc.owner_id.id
        if partner:
            par = partner if isinstance(partner, models.BaseModel) else \
                self.env['res.partner'].browse(int(partner))
            if par:
                vals['partner_id'] = par.id
        if vals:
            self.write(vals)
        return super()._capture_context(object_ref=object_ref)

    def _session_capture_context(self):
        """Core-hook: härled partner via resolver-strategin."""
        self.ensure_one()
        try:
            _fieldservice_partner_strategy(self)
        except Exception as e:
            _logger.warning('session capture (fieldservice) failed: %s', e)
        return super()._session_capture_context()

    def _session_auto_capture(self, prompt):
        """Deterministisk kontextfångst ur användarens prompt.

        - `arbetsorder <id>` / `order <id>` / `FSM<nummer>` → order

        Fångar bara när order saknas ('senast arbetad kontext vinner').
        Tyst no-op vid fel — hooks får aldrig kasta.
        """
        self.ensure_one()
        try:
            text = (prompt or '').strip()
            if not text:
                return super()._session_auto_capture(prompt)
            if not self.fsm_order_id:
                m = re.search(
                    r'(?:arbetsorder|order)\s*#?\s*(\d+)', text, re.I)
                if m:
                    o = self.env['fsm.order'].browse(int(m.group(1)))
                    if o.exists():
                        self._capture_context(fsm_order=o)
                        return super()._session_auto_capture(prompt)
        except Exception as e:
            _logger.warning(
                'session auto-capture (fieldservice) failed: %s', e)
        return super()._session_auto_capture(prompt)
