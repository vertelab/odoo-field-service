from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    fsm_order_id = fields.Many2one(
        'fieldservice.order',
        string='Field Service Order',
        index=True,
        help='Order this timesheet line was logged against. Setting it '
             'fills in the project, task and analytic distribution.',
    )

    @api.onchange('fsm_order_id')
    def _onchange_fsm_order_id(self):
        if not self.fsm_order_id:
            return
        self.project_id = self.fsm_order_id.project_id
        self.task_id = self.fsm_order_id.task_id
        if self.fsm_order_id.analytic_distribution:
            self.analytic_distribution = (
                self.fsm_order_id.analytic_distribution
            )
