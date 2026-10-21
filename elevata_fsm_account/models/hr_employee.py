from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    bill_count = fields.Integer(
        string="Vendor Bills", compute='_compute_bill_count'
    )

    def _compute_bill_count(self):
        for employee in self:
            partner = employee.work_contact_id or employee.user_id.partner_id
            employee.bill_count = self.env['account.move'].search_count([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'in_invoice'),
                ('fsm_order_ids', '!=', False),
            ]) if partner else 0

    def action_view_bills(self):
        self.ensure_one()
        partner = self.work_contact_id or self.user_id.partner_id
        action = self.env['ir.actions.act_window']._for_xml_id(
            'account.action_move_in_invoice_type'
        )
        action['domain'] = [
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'in_invoice'),
            ('fsm_order_ids', '!=', False),
        ]
        return action
