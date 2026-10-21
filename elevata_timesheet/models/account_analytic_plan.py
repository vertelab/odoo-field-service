# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'

    @api.model
    def _elevata_get_or_create_plan(self, name):
        """Return the analytic plan with this name, creating it if missing.

        Called from data/project_data.xml so the seed data stays idempotent
        on databases where the plan already exists.
        """
        plan = self.search([('name', '=', name)], limit=1)
        if not plan:
            plan = self.create({
                'name': name,
                'default_applicability': 'optional',
            })
        return plan.id
