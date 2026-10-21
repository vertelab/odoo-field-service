from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OfferTemplateWizard(models.TransientModel):
    _name = 'elevata.offer.template.wizard'
    _description = 'Välj offertmall'

    offer_id = fields.Many2one(
        'elevata.offer',
        string='Offert',
        required=True,
    )
    offer_type = fields.Selection(
        related='offer_id.offer_type',
        string='Offerttyp',
    )
    template_id = fields.Many2one(
        'elevata.offer.template',
        string='Mall',
        required=True,
        domain="[('offer_type', '=', offer_type)]",
    )

    def action_apply(self):
        self.ensure_one()
        if not self.template_id:
            raise UserError(_('Välj en mall först.'))
        self.offer_id.apply_template(self.template_id)
        return {'type': 'ir.actions.client', 'tag': 'reload'}
