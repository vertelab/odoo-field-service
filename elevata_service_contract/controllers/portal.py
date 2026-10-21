from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class ElevataPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        commercial = partner.commercial_partner_id

        if 'elevator_count' in counters:
            values['elevator_count'] = request.env['maintenance.equipment'].search_count([
                ('customer_id', 'child_of', commercial.id),
                ('elevator_type_id', '!=', False),
            ])
        if 'contract_count' in counters:
            values['contract_count'] = request.env['elevata.service.contract'].search_count([
                ('partner_id', 'child_of', commercial.id),
                ('state', '=', 'confirmed'),
            ])
        if 'workorder_count' in counters:
            values['workorder_count'] = request.env['fieldservice.order'].search_count([
                ('equipment_id.customer_id', 'child_of', commercial.id),
            ])
        if 'invoice_count' in counters:
            values['invoice_count'] = request.env['account.move'].search_count([
                ('partner_id', 'child_of', commercial.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel'),
            ])
        return values

    # ── Hissar ───────────────────────────────────────────────────────────
    @http.route(['/my/elevators', '/my/elevators/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_elevators(self, page=1, **kwargs):
        partner = request.env.user.partner_id
        domain = [
            ('customer_id', 'child_of', partner.commercial_partner_id.id),
            ('elevator_type_id', '!=', False),
        ]
        total = request.env['maintenance.equipment'].search_count(domain)
        pager = portal_pager(url='/my/elevators', total=total, page=page, step=10)
        elevators = request.env['maintenance.equipment'].search(
            domain, order='name asc', limit=10, offset=pager['offset'])
        return request.render('elevata_service_contract.portal_my_elevators', {
            'elevators': elevators,
            'page_name': 'elevators',
            'pager': pager,
        })

    # ── Avtal ────────────────────────────────────────────────────────────
    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_contracts(self, page=1, **kwargs):
        partner = request.env.user.partner_id
        domain = [
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('state', '=', 'confirmed'),
        ]
        total = request.env['elevata.service.contract'].search_count(domain)
        pager = portal_pager(url='/my/contracts', total=total, page=page, step=10)
        contracts = request.env['elevata.service.contract'].search(
            domain, order='id desc', limit=10, offset=pager['offset'])
        return request.render('elevata_service_contract.portal_my_contracts', {
            'contracts': contracts,
            'page_name': 'contracts',
            'pager': pager,
        })

    # ── Arbetsorder ───────────────────────────────────────────────────────
    @http.route(['/my/workorders', '/my/workorders/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_workorders(self, page=1, **kwargs):
        partner = request.env.user.partner_id
        domain = [('equipment_id.customer_id', 'child_of', partner.commercial_partner_id.id)]
        total = request.env['fieldservice.order'].search_count(domain)
        pager = portal_pager(url='/my/workorders', total=total, page=page, step=15)
        orders = request.env['fieldservice.order'].search(
            domain, order='id desc', limit=15, offset=pager['offset'])
        return request.render('elevata_service_contract.portal_my_workorders', {
            'orders': orders,
            'page_name': 'workorders',
            'pager': pager,
        })

    # ── Servicerapport PDF ────────────────────────────────────────────
    @http.route('/my/workorders/<int:order_id>/pdf', type='http', auth='user', website=True)
    def portal_download_service_report(self, order_id, **kwargs):
        partner = request.env.user.partner_id
        order = request.env['fieldservice.order'].browse(order_id)
        if not order.exists() or order.equipment_id.customer_id.commercial_partner_id != partner.commercial_partner_id:
            return request.not_found()
        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'elevata_service_contract.report_fsm_order_service', [order_id]
        )
        filename = 'ServiceReport-%s.pdf' % order.name.replace('/', '-')
        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename="%s"' % filename),
            ]
        )

    # ── Arbetsorder detalj ───────────────────────────────────────────────
    @http.route('/my/workorders/<int:order_id>', type='http', auth='user', website=True)
    def portal_workorder_detail(self, order_id, **kwargs):
        partner = request.env.user.partner_id
        order = request.env['fieldservice.order'].browse(order_id)
        if (not order.exists()
                or order.equipment_id.customer_id.commercial_partner_id
                != partner.commercial_partner_id):
            return request.not_found()
        return request.render('elevata_service_contract.portal_workorder_detail', {
            'order': order,
            'page_name': 'workorders',
        })

    # ── Felanmälan ────────────────────────────────────────────────────────
    @http.route('/my/report-problem', type='http', auth='user', website=True)
    def portal_report_problem_form(self, **kwargs):
        partner = request.env.user.partner_id
        elevators = request.env['maintenance.equipment'].search([
            ('customer_id', 'child_of', partner.commercial_partner_id.id),
            ('elevator_type_id', '!=', False),
        ], order='name asc')
        return request.render('elevata_service_contract.portal_report_problem', {
            'elevators': elevators,
            'page_name': 'report_problem',
            'submitted': False,
            'error': kwargs.get('error'),
        })

    @http.route('/my/report-problem/submit', type='http', auth='user',
                website=True, methods=['POST'])
    def portal_report_problem_submit(self, equipment_id=None, description=None, **kwargs):
        partner = request.env.user.partner_id
        if not equipment_id or not description:
            return request.redirect('/my/report-problem?error=missing')

        location = request.env['maintenance.equipment'].browse(int(equipment_id))
        if not location.exists():
            return request.redirect('/my/report-problem?error=invalid')

        felsok_type = request.env.ref(
            'elevata_order_types.fsm_order_type_repair', raise_if_not_found=False)

        request.env['fieldservice.order'].create({
            'equipment_id': location.id,
            'customer_id': partner.commercial_partner_id.id,
            'description': description,
            'type': felsok_type.id if felsok_type else False,
            'request_early': False,
        })

        elevators = request.env['maintenance.equipment'].search([
            ('customer_id', 'child_of', partner.commercial_partner_id.id),
            ('elevator_type_id', '!=', False),
        ], order='name asc')
        return request.render('elevata_service_contract.portal_report_problem', {
            'elevators': elevators,
            'page_name': 'report_problem',
            'submitted': True,
        })
