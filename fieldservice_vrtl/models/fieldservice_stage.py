from odoo import api, fields, models, _

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

    order_line_ids = fields.Many2one('fieldservice.order', string='Order', store=True)
    order_id = fields.Many2one('fieldservice.order.line', string='Order line', store=True)
    type = fields.Selection([
        ('none', 'None'),
        ('start', 'Start'),
        ('end', 'End')
    ], string="State", default='none')


    
    @api.model
    def create_fakturerad_stage(self):
        existing_stage = self.search([('name', '=', 'Fakturerad')], limit=1)
        if not existing_stage:
            self.create({
                'name': 'Fakturerad',
                'sequence': 20,  
                'fold': True,  
                'is_closed': False, 
                'description': _('This is the Fakturerad stage.'),
            })