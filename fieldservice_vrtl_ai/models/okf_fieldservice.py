# -*- coding: utf-8 -*-
"""fieldservice.order — OKF-indexerbar (fieldservice_vrtl_ai).

VARFOR: en faltsserviceorder AR kunskap om vad som ska goras pa plats och
varfor. `description` (Text) och `name` ligger i kolumner som varken BM25
eller embeddings ser.

Modellen ager sina KALLOR; `ai.okf.mixin` ager falten och flaggan.

OBS om `_inherits`: `fieldservice.order` delegerar till `project.task`
(`_inherits = {'project.task': 'task_id'}`). Det ar DELEGATION — falt pa
`project.task` kopieras inte hit, och en mixin pa `project.task` nar inte
fram. Matt 2026-10-21: `project_task` hade okf-falten, `fieldservice_order`
hade inga. Mixinen laggs darfor explicit har.
"""

from odoo import models, fields


class FieldServiceOrder(models.Model):
    _name = 'fieldservice.order'
    _inherit = ['fieldservice.order', 'ai.okf.mixin']

    # OKF-taggar: egen relationstabell (en many2many kan inte ligga
    # pa en abstrakt mixin — den ger samma tabell for alla arvande).
    okf_tags = fields.Many2many(
        'ai.okf.tag', 'fieldservice_order_okf_tag_rel', 'res_id', 'tag_id',
        string='OKF Tags')

    # ── Kallor ────────────────────────────────────────────────────────────
    #
    # `okf_body`  generisk: `name` + `description`
    # `okf_tags`  generisk: `tag_ids` (malmodellen field.service.order.tag)
    # `okf_links` generisk: `partner_id` (res.partner bar mixinen via
    #             base_ai), `company_id`, `project_id` (via task_id)

    def _okf_artifact_type(self):
        """Bryggans egen typ (okf-mixin D12)."""
        return 'fieldservice_order'

    def _okf_dirty_fields(self):
        """Falt vars andring gor OKF-falten inaktuella.

        `stage_id` ingar: etappen ar en del av ordens mening (samma skal
        som `project.task` i project_ai).
        `requested_employee_ids` ingar: vem som ska ut ar en del av
        innehallet, inte en raknare.
        Datum utan innehall (date_start/date_end) utesluts.
        """
        return {'name', 'description', 'stage_id', 'priority',
                'partner_id', 'requested_employee_ids', 'company_id',
                'active'}

    def _okf_skip_reason(self):
        """Arkiverad order = "tomt just nu", inte "tomt for alltid"."""
        return None

    # ── Registrering (okf-mixin D11) ──────────────────────────────────────

    def _register_hook(self):
        """Registrera modellen for dirty-indexering.

        Registrering, inte overridning: `_okf_indexable_models()` ar
        `@api.model` pa en abstrakt modell.
        """
        res = super()._register_hook()
        self.env['ai.okf.mixin']._okf_register_indexable('fieldservice.order')
        return res
