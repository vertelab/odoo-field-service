from odoo import api, fields, models, _
from datetime import date as date_type
from datetime import datetime, timedelta


class FieldserviceSLA(models.Model):
    _name = 'fieldservice.sla'
    _description = 'Field Service SLA Module'

    name = fields.Char(string='SLA Schema', required=True)
    severity_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'Critic')
    ], string='Allvarlighetsgrad', required=True)

    order_id = fields.Many2one('fieldservice.order', string='Field Service Order')
    # sla_priority = fields.Selection(related='order_id.priority', string='Priority', store = True)
    create_date = fields.Datetime(related='order_id.create_date', readonly=True)
    description = fields.Text(string='Description')
    time_within = fields.Float(string ='Time Within', required=True)

    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        required=True, 
        default=lambda self: self.env.company
    )

    stage_id = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Stage', tracking=True, default='draft'
        )
