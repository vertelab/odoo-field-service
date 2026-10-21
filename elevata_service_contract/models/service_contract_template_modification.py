from odoo import fields, models


class ServiceContractTemplateModification(models.Model):
    _name = 'elevata.service.contract.template.modification'
    _description = 'Service Contract Template Modification'
    _order = 'modification_date desc'

    service_contract_id = fields.Many2one(
        'elevata.service.contract',
        string='Service Contract',
        required=True,
        ondelete='cascade',
    )
    template_id = fields.Many2one(
        'elevata.contract.template',
        string='Template',
        required=True,
    )
    modification_date = fields.Datetime(
        string='Modification Date',
        default=fields.Datetime.now,
        required=True,
    )
    modified_by = fields.Many2one(
        'res.users',
        string='Modified By',
        default=lambda self: self.env.user,
        required=True,
    )
    changes_description = fields.Text(
        string='Changes Description',
        required=True,
    )
