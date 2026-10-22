# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import secrets

from odoo import _, api, fields, models


class MaintenanceEquipment(models.Model):
    """Portal token on the asset.

    A tenant or a passer-by standing at a broken asset has no account and no patience
    for one. A QR code on the asset opens the fault report for that record
    with a token in the URL.

    The token identifies the asset, not the person: it grants the right
    to file a report against this one record and nothing else. It is
    revocable — regenerating it invalidates every printed sticker.
    """

    _inherit = 'maintenance.equipment'

    portal_token = fields.Char(
        string='Portal Token',
        copy=False,
        index=True,
        readonly=True,
        help='Printed in the QR code. Grants fault reporting for this '
             'asset only, without login.',
    )
    portal_report_url = fields.Char(
        string='Fault Report URL',
        compute='_compute_portal_report_url',
    )

    @api.model
    def _generate_portal_token(self):
        return secrets.token_urlsafe(24)

    def _ensure_portal_token(self):
        for equipment in self:
            if not equipment.portal_token:
                equipment.portal_token = self._generate_portal_token()

    def action_generate_portal_token(self):
        """Issue a new token, invalidating the old QR sticker."""
        for equipment in self:
            equipment.portal_token = self._generate_portal_token()

    def _compute_portal_report_url(self):
        base = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', '')
        for equipment in self:
            if equipment.portal_token:
                equipment.portal_report_url = '%s/my/equipment/report/%s' % (
                    base.rstrip('/'), equipment.portal_token)
            else:
                equipment.portal_report_url = False
