from odoo import api, fields, models


class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        compute='_compute_analytic_account_id',
        store=True,
        readonly=False,
        help='Defaults from the project, falls back to the elevator\'s '
             'property. Used to distribute invoice lines and timesheets.',
    )

    @api.depends('project_id.account_id', 'equipment_id.property_id')
    def _compute_analytic_account_id(self):
        for order in self:
            account = order.project_id.account_id
            if not account and order.equipment_id.property_id:
                account = order.equipment_id.property_id.analytic_account_id
            order.analytic_account_id = account

    @api.depends('analytic_account_id')
    def _compute_analytic_distribution(self):
        for order in self:
            order.analytic_distribution = (
                {str(order.analytic_account_id.id): 100.0}
                if order.analytic_account_id else False
            )

    analytic_distribution = fields.Json(
        string='Analytic Distribution',
        compute='_compute_analytic_distribution',
        store=True,
        readonly=False,
        help='Ready-to-use analytic_distribution for invoice lines and '
             'timesheets created from this order.',
    )
