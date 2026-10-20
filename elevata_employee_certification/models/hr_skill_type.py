from odoo import models, fields


class HrSkillType(models.Model):
    _inherit = 'hr.skill.type'

    is_certification = fields.Boolean(
        string='Is Certification Type',
        help='Mark if this skill type represents certifications with expiry dates.',
    )
