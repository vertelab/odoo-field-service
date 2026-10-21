from odoo import fields, models


class ServiceContractVersion(models.Model):
    _name = 'elevata.service.contract.version'
    _description = 'Service Contract Version'
    _order = 'version_number desc'

    service_contract_id = fields.Many2one(
        'elevata.service.contract',
        string='Contract',
        required=True,
        ondelete='cascade',
    )
    version_number = fields.Integer(
        string='Version Number',
        required=True,
    )
    version_date = fields.Datetime(
        string='Version Date',
        default=fields.Datetime.now,
        required=True,
    )
    change_description = fields.Text(
        string='Changes Description',
        help='Description of changes made in this version',
    )
    customer_feedback = fields.Text(
        string='Customer Feedback',
        help='Feedback received from customer',
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
    )
    approved_date = fields.Datetime(
        string='Approval Date',
    )
    html_content = fields.Html(
        string='HTML Content',
        sanitize=False,
    )
    pdf_content = fields.Binary(
        string='PDF Content',
        attachment=True,
    )
    pdf_filename = fields.Char(
        string='PDF Filename',
    )

    def _compute_display_name(self):
        for version in self:
            version.display_name = (
                "%s (V%s)" % (
                    version.service_contract_id.name,
                    version.version_number,
                )
            )
