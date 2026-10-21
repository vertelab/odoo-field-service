from odoo import models, fields, api


MILESTONE_STATE = [
    ('pending', 'Väntar'),
    ('invoiced', 'Fakturerad'),
    ('paid', 'Betald'),
]


class ElevataOfferMilestone(models.Model):
    _name = 'elevata.offer.milestone'
    _description = 'Elevata Offert Milstolpe'
    _order = 'sequence, id'

    offer_id = fields.Many2one(
        'elevata.offer',
        string='Offert',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Milstolpe', required=True)
    percentage = fields.Float(string='Andel (%)', digits=(5, 2))
    amount = fields.Float(
        string='Belopp',
        compute='_compute_amount',
        store=True,
        digits=(16, 2),
    )
    state = fields.Selection(
        MILESTONE_STATE,
        string='Status',
        default='pending',
        required=True,
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Faktura',
        readonly=True,
        copy=False,
    )
    invoice_state = fields.Selection(
        related='invoice_id.state',
        string='Fakturastatus',
    )

    @api.depends('percentage', 'offer_id.amount_untaxed')
    def _compute_amount(self):
        for ms in self:
            ms.amount = (ms.percentage / 100.0) * ms.offer_id.amount_untaxed
