# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class EquipmentPortal(CustomerPortal):
    """Customer portal for assets.

    Every route scopes to the logged-in partner's commercial entity and
    re-checks the record before rendering: a guessed id gives 404, never
    another customer's asset.
    """

    def _equipment_domain(self):
        partner = request.env.user.partner_id
        return [
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
        ]

    def _get_equipment(self, equipment_id):
        """Fetch an asset, or None when it is not the caller's."""
        equipment = request.env['maintenance.equipment'].browse(equipment_id)
        if not equipment.exists():
            return None
        partner = request.env.user.partner_id
        if equipment.partner_id.commercial_partner_id != partner.commercial_partner_id:
            return None
        return equipment

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'equipment_count' in counters:
            values['equipment_count'] = request.env[
                'maintenance.equipment'].search_count(self._equipment_domain())
        return values

    # ── List ─────────────────────────────────────────────────────────────
    @http.route(['/my/equipment', '/my/equipment/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_equipment(self, page=1, **kwargs):
        domain = self._equipment_domain()
        total = request.env['maintenance.equipment'].search_count(domain)
        pager = portal_pager(
            url='/my/equipment', total=total, page=page, step=10)
        equipment_list = request.env['maintenance.equipment'].search(
            domain, order='name asc', limit=10, offset=pager['offset'])
        return request.render('fieldservice_portal.portal_my_equipment', {
            'equipment_list': equipment_list,
            'page_name': 'equipment',
            'pager': pager,
        })

    # ── Detail ───────────────────────────────────────────────────────────
    @http.route('/my/equipment/<int:equipment_id>',
                type='http', auth='user', website=True)
    def portal_equipment_detail(self, equipment_id, **kwargs):
        equipment = self._get_equipment(equipment_id)
        if not equipment:
            return request.not_found()
        return request.render('fieldservice_portal.portal_equipment_detail', {
            'equipment': equipment,
            'page_name': 'equipment',
        })

    # ── Fault report, logged in ──────────────────────────────────────────
    @http.route('/my/equipment/<int:equipment_id>/report',
                type='http', auth='user', website=True)
    def portal_report_form(self, equipment_id, **kwargs):
        equipment = self._get_equipment(equipment_id)
        if not equipment:
            return request.not_found()
        return request.render('fieldservice_portal.portal_report_form', {
            'equipment': equipment,
            'page_name': 'equipment',
            'error': kwargs.get('error'),
        })

    @http.route('/my/equipment/<int:equipment_id>/report/submit',
                type='http', auth='user', website=True, methods=['POST'])
    def portal_report_submit(self, equipment_id, description=None, **kwargs):
        equipment = self._get_equipment(equipment_id)
        if not equipment:
            return request.not_found()
        if not description or not description.strip():
            return request.redirect(
                '/my/equipment/%s/report?error=missing' % equipment_id)
        self._create_fault_order(equipment, description.strip())
        return request.render('fieldservice_portal.portal_report_done', {
            'equipment': equipment,
            'page_name': 'equipment',
        })

    # ── Fault report, QR token (no login) ────────────────────────────────
    @http.route('/my/equipment/report/<string:token>',
                type='http', auth='public', website=True)
    def portal_report_by_token(self, token, **kwargs):
        """Open the fault report for the asset the token belongs to.

        auth='public': a tenant has no account. The token identifies the
        asset and nothing else — it cannot be used to read the record.
        """
        equipment = request.env['maintenance.equipment'].sudo().search([
            ('portal_token', '=', token),
            ], limit=1)
        if not equipment:
            return request.not_found()
        return request.render('fieldservice_portal.portal_report_token', {
            'equipment': equipment,
            'token': token,
            'error': kwargs.get('error'),
        })

    @http.route('/my/equipment/report/<string:token>/submit',
                type='http', auth='public', website=True, methods=['POST'])
    def portal_report_token_submit(self, token, description=None,
                                   reporter_name=None, reporter_phone=None,
                                   **kwargs):
        equipment = request.env['maintenance.equipment'].sudo().search([
            ('portal_token', '=', token),
            ], limit=1)
        if not equipment:
            return request.not_found()
        if not description or not description.strip():
            return request.redirect(
                '/my/equipment/report/%s?error=missing' % token)

        self._create_fault_order(
            equipment, description.strip(),
            reporter_name=reporter_name, reporter_phone=reporter_phone)
        return request.render('fieldservice_portal.portal_report_done', {
            'equipment': equipment,
            'page_name': 'equipment',
            'from_token': True,
        })

    # ── Shared ───────────────────────────────────────────────────────────
    def _create_fault_order(self, equipment, description,
                            reporter_name=None, reporter_phone=None):
        """Create the work order the technician will see.

        The order type is the repair type when it exists. Without one the
        order is still created — a fault report must never be lost because
        a type record is missing.
        """
        order_type = request.env['fieldservice.order.type'].sudo().search(
            [('name', 'ilike', 'repair')], limit=1)
        vals = {
            'name': _('Fault report — %s', equipment.display_name),
            'equipment_id': equipment.id,
            'description': description,
            'partner_id': equipment.partner_id.id,
        }
        if order_type:
            vals['product_type'] = order_type.id
        # reporter_phone exists on fieldservice.order via elevata_fsm_flow.
        # A name has nowhere to go without a partner record, so it is
        # prepended to the description instead of inventing a field.
        if reporter_name:
            vals['description'] = '%s\n\nRapporterat av: %s' % (
                description, reporter_name)
        if reporter_phone and 'reporter_phone' in request.env[
                'fieldservice.order']._fields:
            vals['reporter_phone'] = reporter_phone
        return request.env['fieldservice.order'].sudo().create(vals)
