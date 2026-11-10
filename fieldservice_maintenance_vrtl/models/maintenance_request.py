from odoo import models, fields, api, _
from odoo.tools import html2plaintext


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    fieldservice_order_id = fields.Many2one(
        'fieldservice.order',
        string='Field Service Order',
        copy=False,
        ondelete='set null',
        index=True,
        help='The field service order that dispatches this work to a technician.',
    )
    fieldservice_order_count = fields.Integer(
        string='Field Service Orders',
        compute='_compute_fieldservice_order_count',
    )

    @api.depends('fieldservice_order_id')
    def _compute_fieldservice_order_count(self):
        for request in self:
            request.fieldservice_order_count = 1 if request.fieldservice_order_id else 0

    def action_create_fieldservice_order(self):
        """Create a field service order for this maintenance request.

        The two records keep separate lifecycles: the request tracks the
        maintenance work, the order tracks the dispatch. Linking them does
        not make one follow the other.

        The description is converted from HTML to plain text because
        maintenance.request.description is Html while
        fieldservice.order.description is Text.
        """
        self.ensure_one()

        if self.fieldservice_order_id:
            return self.action_view_fieldservice_order()

        description = html2plaintext(self.description) if self.description else False

        order = self.env['fieldservice.order'].create({
            'name': self.name,
            'description': description,
            'partner_id': self._get_fieldservice_partner().id or False,
            'maintenance_request_id': self.id,
            'equipment_id': self.equipment_id.id or False,
        })

        self.fieldservice_order_id = order.id

        return {
            'name': _('Field Service Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'fieldservice.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _get_fieldservice_partner(self):
        """Find the partner the field service order should be addressed to.

        Prefer the equipment's owner, then the request's own owner. Falls
        back to an empty recordset.
        """
        self.ensure_one()
        if self.equipment_id and self.equipment_id.partner_id:
            return self.equipment_id.partner_id
        if self.owner_user_id and self.owner_user_id.partner_id:
            return self.owner_user_id.partner_id
        return self.env['res.partner']

    def action_view_fieldservice_order(self):
        self.ensure_one()
        return {
            'name': _('Field Service Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'fieldservice.order',
            'res_id': self.fieldservice_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
