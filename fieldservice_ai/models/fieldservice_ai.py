# -*- coding: utf-8 -*-
"""Field Service-verktyg — affärslogik för arbetsorder.

Mönstret är project_ai:s: verktygen i XML är tunna skal som anropar
metoder här. Logiken ligger i modellen, inte i sandbox-koden.

`fsm.order` har ingen `partner_id` — kunden nås via
`location_id.partner_id`, eftersom `fsm.location` ärver `res.partner`.
"""

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class FieldServiceAI(models.AbstractModel):
    _name = 'fieldservice.ai'
    _description = 'Field Service AI — business logic for the order tools'

    # ── Kontext ────────────────────────────────────────────────────────

    @api.model
    def _capture_session_from_order(self, order_id):
        """Tagga den aktuella sessionen med order/plats/kund-kontext."""
        try:
            if self.env.context.get('_ai_context_model') != \
                    'ai.coworker.session':
                return self.env['ai.coworker.session']
            sess = self.env['ai.coworker.session'].browse(
                int(self.env.context.get('_ai_context_id') or 0))
            if not sess.exists():
                return self.env['ai.coworker.session']
            sess._capture_context(fsm_order=order_id)
            return sess
        except Exception as e:
            _logger.warning('session capture from order failed: %s', e)
            return self.env['ai.coworker.session']

    # ── Läsning ────────────────────────────────────────────────────────

    @api.model
    def order_get(self, order_id):
        """Returnera arbetsorderinfo (dict)."""
        order = self.env['fsm.order'].sudo().browse(int(order_id))
        if not order.exists():
            return {'error': 'Order %s not found' % order_id}
        self._capture_session_from_order(order.id)
        location = order.location_id
        return {
            'id': order.id,
            'name': order.name,
            'stage': order.stage_id.name if order.stage_id else '',
            'is_closed': order.is_closed,
            'priority': order.priority,
            'team': order.team_id.name if order.team_id else '',
            'location_id': location.id if location else None,
            'location_name': location.display_name if location else '',
            # Kunden är owner_id — fsm.location ÄRVER res.partner, så
            # partner_id är platsens egen post, inte kundens.
            'partner_id': location.owner_id.id
                          if location and location.owner_id else None,
            'partner_name': location.owner_id.name
                            if location and location.owner_id else '',
            'street': location.street if location else '',
            'city': location.city if location else '',
            'person_ids': [p.id for p in order.person_ids]
                          if 'person_ids' in order._fields else [],
            'request_early': order.request_early.isoformat()
                             if order.request_early else None,
            'description': (order.description or '')[:500]
                           if 'description' in order._fields else '',
        }

    # ── Skrivning ──────────────────────────────────────────────────────

    @api.model
    def order_set_stage(self, order_id, stage):
        """Flytta arbetsordern till en etapp. Returnerar (ok, meddelande)."""
        order = self.env['fsm.order'].sudo().browse(int(order_id))
        if not order.exists():
            return False, 'Order %s not found' % order_id
        wanted = str(stage or '').strip()
        if not wanted:
            return False, 'Missing stage name'
        found = self.env['fsm.stage'].sudo().search(
            [('name', '=ilike', wanted)], limit=1)
        if not found:
            return False, 'No stage named %r' % stage
        order.write({'stage_id': found.id})
        self._capture_session_from_order(order.id)
        return True, 'Order %s moved to stage %s' % (
            order.name, found.name)

    @api.model
    def order_update_fields(self, order_id, priority=None, description=None):
        """Uppdatera prioritet och/eller beskrivning."""
        order = self.env['fsm.order'].sudo().browse(int(order_id))
        if not order.exists():
            return False, 'Order %s not found' % order_id
        vals = {}
        if priority is not None and str(priority).strip():
            vals['priority'] = str(priority).strip()
        if description is not None and 'description' in order._fields:
            vals['description'] = str(description)
        if not vals:
            return False, 'Nothing to update'
        order.write(vals)
        self._capture_session_from_order(order.id)
        return True, 'Order %s updated: %s' % (
            order.name, ', '.join(sorted(vals)))

    @api.model
    def order_add_message(self, order_id, body):
        """Posta ett meddelande i arbetsorderns chatter."""
        order = self.env['fsm.order'].sudo().browse(int(order_id))
        if not order.exists():
            return False, 'Order %s not found' % order_id
        if not body or not str(body).strip():
            return False, 'Missing message body'
        order.message_post(body=str(body), message_type='comment')
        self._capture_session_from_order(order.id)
        return True, 'Message posted on %s' % order.name
