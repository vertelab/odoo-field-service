from odoo import models, fields, api, _
from datetime import date, timedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    certification_skill_ids = fields.One2many(
        'hr.employee.skill',
        'employee_id',
        domain="[('skill_type_id.is_certification', '=', True)]",
        string='Certifications',
    )

    cert_count = fields.Integer(
        string='Certifications',
        compute='_compute_cert_counts',
    )
    cert_expired_count = fields.Integer(
        string='Expired',
        compute='_compute_cert_counts',
    )

    @api.depends('certification_skill_ids.cert_status')
    def _compute_cert_counts(self):
        for emp in self:
            certs = emp.certification_skill_ids
            emp.cert_count = len(certs)
            emp.cert_expired_count = len(
                certs.filtered(lambda s: s.cert_status in ('expired', 'expiring'))
            )

    def action_view_certifications(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Certifications — %s') % self.name,
            'res_model': 'hr.employee.skill',
            'view_mode': 'list,form',
            'domain': [
                ('employee_id', '=', self.id),
                ('skill_type_id.is_certification', '=', True),
            ],
            'context': {'default_employee_id': self.id},
        }

    def _cron_check_certifications(self):
        today = date.today()
        soon = today + timedelta(days=60)
        # Refresh the stored cert_status for every certification with an expiry date
        all_certs = self.env['hr.employee.skill'].search([
            ('skill_type_id.is_certification', '=', True),
            ('date_expiry', '!=', False),
        ])
        all_certs._compute_cert_status()
        expiring = self.env['hr.employee.skill'].search([
            ('skill_type_id.is_certification', '=', True),
            ('date_expiry', '>=', today.strftime('%Y-%m-%d')),
            ('date_expiry', '<=', soon.strftime('%Y-%m-%d')),
        ])
        for rec in expiring:
            existing = self.env['mail.activity'].search([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', rec.employee_id.id),
                ('summary', 'ilike', rec.skill_id.name),
            ], limit=1)
            if existing:
                continue
            manager_uid = (
                rec.employee_id.parent_id.user_id.id
                if rec.employee_id.parent_id and rec.employee_id.parent_id.user_id
                else self.env.uid
            )
            rec.employee_id.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=rec.date_expiry - timedelta(days=30),
                summary='Certification expiring: %s' % rec.skill_id.name,
                note='Certification <b>%s</b> for <b>%s</b> expires <b>%s</b>. Renew in time!' % (
                    rec.skill_id.name,
                    rec.employee_id.name,
                    rec.date_expiry.strftime('%Y-%m-%d'),
                ),
                user_id=manager_uid,
            )
