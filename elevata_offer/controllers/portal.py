from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class OfferPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'offer_count' in counters:
            partner = request.env.user.partner_id
            values['offer_count'] = request.env['elevata.offer'].search_count([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['sent', 'negotiation', 'won', 'lost']),
            ])
        return values

    @http.route('/my/offers', type='http', auth='user', website=True)
    def portal_my_offers(self, **kw):
        partner = request.env.user.partner_id
        offers = request.env['elevata.offer'].search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sent', 'negotiation', 'won', 'lost']),
        ], order='id desc')
        return request.render('elevata_offer.portal_my_offers', {
            'offers': offers,
            'page_name': 'offers',
        })

    @http.route('/my/offer/<int:offer_id>', type='http', auth='user', website=True)
    def portal_offer_detail(self, offer_id, **kw):
        partner = request.env.user.partner_id
        offer = request.env['elevata.offer'].search([
            ('id', '=', offer_id),
            ('partner_id', '=', partner.id),
        ], limit=1)
        if not offer:
            return request.redirect('/my/offers')
        return request.render('elevata_offer.portal_offer_detail', {
            'offer': offer,
            'page_name': 'offer_detail',
        })

    @http.route('/my/offer/<int:offer_id>/accept', type='http', auth='user',
                methods=['POST'], website=True, csrf=True)
    def portal_offer_accept(self, offer_id, **kw):
        partner = request.env.user.partner_id
        offer = request.env['elevata.offer'].search([
            ('id', '=', offer_id),
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sent', 'negotiation']),
        ], limit=1)
        if offer:
            offer.action_won()
            offer.message_post(
                body=_('Offerten accepterades av kunden via portalen.'),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return request.redirect('/my/offer/%s' % offer_id)
