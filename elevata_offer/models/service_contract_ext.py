from odoo import api, fields, models


class ServiceContractOfferExt(models.Model):
    _inherit = 'elevata.service.contract'

    offer_id = fields.Many2one(
        'elevata.offer',
        string='Offert',
        readonly=True,
        ondelete='set null',
    )
    offer_pdf_url = fields.Char(
        string='Offert-PDF URL',
        compute='_compute_offer_pdf_url',
    )

    @api.depends('offer_id')
    def _compute_offer_pdf_url(self):
        for rec in self:
            if rec.offer_id:
                rec.offer_pdf_url = (
                    '/report/html/elevata_offer.report_offer_document/%d'
                    % rec.offer_id.id
                )
            else:
                rec.offer_pdf_url = False

    def action_open_offer_pdf(self):
        self.ensure_one()
        if not self.offer_id:
            return
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/elevata_offer.report_offer_document/%d' % self.offer_id.id,
            'target': 'new',
        }

    def action_download_offer_pdf(self):
        return self.action_open_offer_pdf()
