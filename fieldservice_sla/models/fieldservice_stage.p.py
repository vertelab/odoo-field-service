from odoo import api, fields, models, _

class FieldServiceStage(models.Model):
    _inherit = 'fieldservice.stage'
    _description = 'Field Service Stage'

    sla_ids = fields.One2many('fieldservice.sla', 'fieldservice_stage', string='SLAs')

    def create_test_sla(self):
        self.env['fieldservice.sla'].create({
            'name': 'Test SLA',
            'stage_id': self.id,   
        })