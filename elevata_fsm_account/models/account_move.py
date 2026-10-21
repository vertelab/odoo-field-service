from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    fsm_order_ids = fields.Many2many(
        'fieldservice.order',
        'fieldservice_order_account_move_rel',
        'move_id',
        'order_id',
        string="Field Service Orders",
        copy=False,
        search='_search_fsm_order_ids',
    )
    fsm_equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Lift',
        index=True,
        copy=False,
        help='Lift this invoice was created from via a work order.',
    )

    def _search_fsm_order_ids(self, operator, value):
        """Search through the line-level link.

        ``fsm_order_ids`` on the move is a convenience view over the lines,
        so searching it must resolve to moves whose lines point at the
        order.
        """
        lines = self.env['account.move.line'].search([
            ('fsm_order_ids', operator, value),
        ])
        return [('line_ids', 'in', lines.ids)]


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    fsm_order_ids = fields.Many2many(
        'fieldservice.order',
        'fieldservice_order_account_move_line_rel',
        'move_line_id',
        'order_id',
        string="Field Service Orders",
        copy=False,
    )
