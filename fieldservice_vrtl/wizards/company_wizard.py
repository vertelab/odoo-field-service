from odoo import models, fields, api

class ChangeCompanyWizard(models.TransientModel):
    _name = 'change.company.wizard'
    _description = 'Wizard to change company on Field Service Order'

    company_id = fields.Many2one('res.company', string='Company', required=True)
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
        if self.model and self.res_id and self.company_id:
            record = self.env[self.model].sudo().browse(self.res_id)
            if record.exists() and 'company_id' in record._fields:
                try:
                    # Ändra företaget direkt utan att använda with_company eller with_context
                    record.company_id = self.company_id.id
                except Exception as e:
                    raise UserError(f"Could not change company: {str(e)}")

        # Hämta bas-URL:en
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        # Konstruera URL:en för Field Service-vyn
        url = f"{base_url}/web#model=fieldservice.order&view_type=kanban"

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self'
        }

