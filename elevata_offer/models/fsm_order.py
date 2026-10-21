from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FSMOrderOfferExt(models.Model):
    _inherit = 'fieldservice.order'

    elevata_offer_id = fields.Many2one(
        'elevata.offer',
        string='Offert',
        compute='_compute_elevata_offer_id',
        store=True,
    )
    elevata_milestone_count = fields.Integer(
        string='Milstolpar',
        compute='_compute_elevata_offer_id',
        store=True,
    )
    elevata_milestone_invoiced_pct = fields.Float(
        string='Fakturerat (%)',
        compute='_compute_elevata_milestone_invoiced_pct',
    )

    @api.depends('elevata_offer_id.milestone_ids', 'elevata_offer_id.milestone_ids.state',
                 'elevata_offer_id.milestone_ids.percentage')
    def _compute_elevata_milestone_invoiced_pct(self):
        for order in self:
            offer = order.elevata_offer_id
            if offer and offer.milestone_ids:
                invoiced = offer.milestone_ids.filtered(
                    lambda m: m.state in ('invoiced', 'paid'))
                order.elevata_milestone_invoiced_pct = sum(invoiced.mapped('percentage'))
            else:
                order.elevata_milestone_invoiced_pct = 0.0

    @api.depends()
    def _compute_elevata_offer_id(self):
        Offer = self.env['elevata.offer']
        for order in self:
            offer = Offer.search([
                ('fsm_order_ids', 'in', order.id),
            ], limit=1)
            order.elevata_offer_id = offer.id if offer else False
            order.elevata_milestone_count = len(offer.milestone_ids) if offer else 0

    def action_view_elevata_milestones(self):
        self.ensure_one()
        offer = self.elevata_offer_id
        if not offer:
            raise UserError(_('Ingen kopplad offert hittades.'))
        invoices = offer.milestone_ids.mapped('invoice_id').filtered(lambda i: i.id)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Milstolpe-fakturor'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoices.ids)],
        }

    def action_invoice_next_elevata_milestone(self):
        self.ensure_one()
        offer = self.elevata_offer_id
        if not offer:
            raise UserError(_('Ingen kopplad offert hittades.'))
        return offer.action_invoice_next_milestone()
