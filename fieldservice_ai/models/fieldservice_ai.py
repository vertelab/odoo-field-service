# -*- coding: utf-8 -*-
"""Field Service — ai.coworker-brygga for faltsserviceorder.

Samma monster som `project_ai.models.project_ai`: metoder pa `ai.coworker`
som coworkern anropar via sina tools. Etapp-slumpningen ar dynamisk (samma
STAGE_PATTERNS som project_ai) eftersom `fieldservice.stage` ar en egen
modell med egna namn per installation.
"""

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# Samma monster som project_ai.STAGE_PATTERNS — faltsserviceetapper heter
# oftast samma saker (Ny, Planerad, Pagar, Utford, Avbruten).
STAGE_PATTERNS = {
    "new": ["ny", "new", "opped"],
    "planned": ["planerad", "planerad", "planned", "schemalagd"],
    "ongoing": ["pagar", "pagaende", "ongoing", "start", "utford"],
    "test": ["test", "kontroll"],
    "done": ["klar", "done", "ok", "utford", "avslutad"],
    "cancelled": ["avbruten", "cancelled", "canceled"],
}


class FieldServiceOrderAICoworker(models.Model):
    _inherit = 'ai.coworker'

    @api.model
    def _fieldservice_find_stage(self, status_key):
        """Dynamiskt sla upp stage_id via namn-matchning mot etapperna."""
        patterns = STAGE_PATTERNS.get(status_key)
        if not patterns:
            return None

        stages = self.env['fieldservice.stage'].search_read(
            [], fields=['id', 'name'])
        for pattern in patterns:
            for s in stages:
                if pattern.lower() in (s['name'] or '').lower():
                    return s['id']
        return None

    @api.model
    def _fieldservice_status_map(self):
        """Mappa en fritextstatus till STAGE_PATTERNS-nyckel."""
        return {
            'new': 'new',
            'opped': 'new',
            'planned': 'planned',
            'scheduled': 'planned',
            'ongoing': 'ongoing',
            'in_progress': 'ongoing',
            'started': 'ongoing',
            'test': 'test',
            'testing': 'test',
            'done': 'done',
            'completed': 'done',
            'closed': 'done',
            'cancelled': 'cancelled',
            'canceled': 'cancelled',
        }

    @api.model
    def fieldservice_order_get(self, order_id):
        """Returnera order-info (JSON) for en faltsserviceorder."""
        order = self.env['fieldservice.order'].sudo().browse(order_id)
        if not order.exists():
            return {'error': 'Order %s not found' % order_id}
        return {
            'id': order.id,
            'name': order.name,
            'partner_id': order.partner_id.id if order.partner_id else None,
            'partner_name': order.partner_id.name if order.partner_id else '',
            'stage': order.stage_id.name if order.stage_id else '',
            'requested_employee_ids': [e.id for e in order.requested_employee_ids],
            'requested_employee_names': [
                e.name for e in order.requested_employee_ids],
            'priority': order.priority,
            'date_start': order.date_start.isoformat() if order.date_start else None,
            'date_end': order.date_end.isoformat() if order.date_end else None,
            'description': (order.description or '')[:500],
        }

    @api.model
    def fieldservice_order_set_status(self, order_id, status):
        """Satt orderstatus via etapp-slumpning. Returnerar (ok, meddelande)."""
        order = self.env['fieldservice.order'].sudo().browse(order_id)
        if not order.exists():
            return False, 'Order %s not found' % order_id
        key = self._fieldservice_status_map().get((status or '').strip().lower())
        if not key:
            return False, 'Unknown status: %s' % status
        stage_id = self._fieldservice_find_stage(key)
        if not stage_id:
            return False, 'No stage found for status %r' % status
        order.write({'stage_id': stage_id})
        return True, 'Order %s moved to stage %s' % (order.name, status)
