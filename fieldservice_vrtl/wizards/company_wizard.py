from odoo import models, fields, api
import logging
class ChangeCompanyWizard(models.TransientModel):
    _name = 'change.company.wizard'
    _description = 'Wizard to change company on Field Service Order'
    #partner_id = fields.Many2one('res.partner', string='Company', required=True,
    #                         domain=[('id', 'in', [])])#
    def _get_company_partners_domain(self):
       company_partners = self.env['res.company'].sudo().search([]).mapped('partner_id')
       return [('id', 'in', company_partners.ids)]

    partner_id = fields.Many2one('res.partner', string='Company', required=True,
                             domain=lambda self: self._get_company_partners_domain())

    #company_id = fields.Many2one('res.company', string='Company', required=True)
    model = fields.Char(string='Model')
    res_id = fields.Integer(string='Resource ID')

    @api.model
    def default_get(self, fields):
        res = super(ChangeCompanyWizard, self).default_get(fields)
        if self.env.context.get('active_model') and self.env.context.get('active_id'):
            res['model'] = self.env.context['active_model']
            res['res_id'] = self.env.context['active_id']
        return res

    def change_company(self):
        self.ensure_one()
        self = self.sudo()
        if self.model and self.res_id and self.partner_id:
            record = self.env[self.model].sudo().browse(self.res_id)
            if record.exists() and 'company_id' in record._fields:
                try:
                    company_id = self.env['res.company'].search([('partner_id','=',self.partner_id.id)])
                    #logging.warning(f"{self.partner_id=}")
                    #logging.warning(f"{company_id=}")
                    record.company_id = company_id.id
                except Exception as e:
                    raise UserError(f"Could not change company: {str(e)}")

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        url = f"{base_url}/web#model=fieldservice.order&view_type=kanban"

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self'
        }

