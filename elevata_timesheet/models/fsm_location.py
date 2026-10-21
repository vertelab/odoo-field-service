from odoo import api, fields, models


class FSMLocation(models.Model):
    _inherit = 'maintenance.equipment'

    elevata_hiss_analytic_id = fields.Many2one(
        'account.analytic.account',
        string="Analytic Account (Elevator Object)",
        domain="[('plan_id', '=', 6)]",
        copy=False,
    )

    def _get_or_create_analytic_account(self):
        self.ensure_one()
        if self.elevata_hiss_analytic_id:
            return self.elevata_hiss_analytic_id
        plan = self.env.ref(
            'elevata_timesheet.analytic_plan_hissobjekt',
            raise_if_not_found=False,
        )
        if not plan:
            return False
        account = self.env['account.analytic.account'].create({
            'name': self.complete_name or self.name or 'Elevator',
            'plan_id': plan.id,
        })
        self.elevata_hiss_analytic_id = account
        return account

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered('is_elevator'):
            record._get_or_create_analytic_account()
        return records
