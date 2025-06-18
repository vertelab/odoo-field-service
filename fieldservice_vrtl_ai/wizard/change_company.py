from odoo import models, fields, api
import logging
class ChangeCompanyWizard(models.TransientModel):
    _inherit = 'change.company.wizard'
    _description = 'Wizard to change company on Field Service Order'

    def change_company(self):
        self.ensure_one()
        self = self.sudo()
        if self.model and self.res_id and self.partner_id:
            record = self.env[self.model].sudo().browse(self.res_id)
            if record.exists() and 'company_id' in record._fields:
                    company_id = self.env['res.company'].search([('partner_id','=',self.partner_id.id)])
                    record.company_id = company_id.id
                    if record.ai_quest_id:
                       self.invite_to_chat(record)
                    new_stage = self.env.ref('fieldservice_vrtl.fieldservice_stage_new')
                    planning_stage = self.env.ref('fieldservice_vrtl.fieldservice_stage_planning')
                    if new_stage and record.stage_id.id == new_stage.id:
                        if planning_stage:
                            record.stage_id = planning_stage
                    
                    

    
    def invite_to_chat(self,record):
        self.ensure_one()
        channel = record.ai_quest_id.channel_id
        if not channel:
            raise UserError(_("No channel found for the AI quest"))

        users = self.env['res.users'].search([('company_ids', 'in', record.company_id.id)])
        partners = users.mapped('partner_id')
        if not partners:
            raise UserError(_("No partners found for users in the company."))

        channel.write({'channel_partner_ids': [(4, pid) for pid in partners.ids]})
        
