from odoo import models, fields, api
from datetime import date, timedelta


class HrEmployeeSkill(models.Model):
    _inherit = 'hr.employee.skill'

    date_issued = fields.Date(string='Date Issued')
    date_expiry = fields.Date(string='Valid Until')
    certificate_number = fields.Char(string='Certificate Number')

    cert_status = fields.Selection([
        ('valid', 'Valid'),
        ('expiring', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('no_date', '–'),
    ], string='Status', compute='_compute_cert_status', store=True)

    @api.depends('date_expiry')
    def _compute_cert_status(self):
        today = date.today()
        soon = today + timedelta(days=60)
        for rec in self:
            if not rec.date_expiry:
                rec.cert_status = 'no_date'
            elif rec.date_expiry < today:
                rec.cert_status = 'expired'
            elif rec.date_expiry <= soon:
                rec.cert_status = 'expiring'
            else:
                rec.cert_status = 'valid'
