# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'

    fsm_recurring_id = fields.Many2one(
        'fsm.recurring',
        string='Recurring Order',
        readonly=True,
        copy=False,
        index=True,
        ondelete='set null',
        help='Template that generated this order, if any.',
    )

    def action_view_fsm_recurring(self):
        """Smart button: open the template that generated this order."""
        self.ensure_one()
        if not self.fsm_recurring_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Recurring Order'),
            'res_model': 'fsm.recurring',
            'res_id': self.fsm_recurring_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
