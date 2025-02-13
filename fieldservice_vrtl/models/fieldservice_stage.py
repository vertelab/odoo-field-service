from odoo import api, fields, models

class FieldServiceStage(models.Model):
    _name = 'fieldservice.stage'
    _description = 'Field Service Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    fold = fields.Boolean(string='Folded in Kanban')
    is_closed = fields.Boolean(string='Closed Stage')
    description = fields.Text(translate=True)
    mail_template_id = fields.Many2one('mail.template', string='Email Template')
    sms_template_id = fields.Many2one('sms.template', string='SMS Template')
