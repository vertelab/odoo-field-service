from odoo import models, fields, api, _

CONTRACT_TYPE = [
    ('SERV-VB', 'Vid Behov'),
    ('SERV-STD', 'Standard'),
    ('SERV-FULL', 'Fullservice'),
    ('SERV-GAR', 'Garanti'),
]


class FSMLocationOfferExt(models.Model):
    _inherit = 'maintenance.equipment'

    elevata_contract_price = fields.Float(
        string='Senast avtalat pris (kr/år)',
        digits=(16, 2),
        help='Sparas automatiskt när offert markeras som vunnen',
    )
    elevata_contract_type = fields.Selection(
        CONTRACT_TYPE,
        string='Aktuell avtalstyp',
    )

    offer_count = fields.Integer(
        string='Offerter',
        compute='_compute_offer_count',
    )

    def _compute_offer_count(self):
        OfferLine = self.env['elevata.offer.line']
        for location in self:
            offer_ids = OfferLine.search([
                ('equipment_id', '=', location.id),
            ]).mapped('offer_id').ids
            location.offer_count = len(set(offer_ids))

    def action_view_offers(self):
        self.ensure_one()
        offer_ids = self.env['elevata.offer.line'].search([
            ('equipment_id', '=', self.id),
        ]).mapped('offer_id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Offerter'),
            'res_model': 'elevata.offer',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', offer_ids)],
        }
