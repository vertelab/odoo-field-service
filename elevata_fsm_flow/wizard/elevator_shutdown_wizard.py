# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ElevatorShutdownWizard(models.TransientModel):
    _name = 'elevata.elevator.shutdown.wizard'
    _description = 'Wizard: registrera hissavstängning'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Hiss',
        required=True,
    )
    operational_status = fields.Selection([
        ('out_of_order', 'Avstängd'),
        ('decommissioned', 'Avställd'),
    ], string='Status', required=True, default='out_of_order')
    out_of_order_date = fields.Date(
        string='Avstängd fr.o.m.',
        default=fields.Date.context_today,
        required=True,
    )
    out_of_order_reason = fields.Text(
        string='Anledning',
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        equipment_id = self.env.context.get('default_equipment_id')
        if equipment_id:
            res['equipment_id'] = equipment_id
        return res

    def action_confirm(self):
        self.ensure_one()
        if not self.equipment_id:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        self.equipment_id.write({
            'operational_status': self.operational_status,
            'out_of_order_date': self.out_of_order_date,
            'out_of_order_reason': self.out_of_order_reason,
        })
        return {'type': 'ir.actions.client', 'tag': 'reload'}
