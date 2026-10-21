# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class FSMOrder(models.Model):
    """Elevata's field service order customisations.

    Ported from Odoo 17 / OCA fieldservice to the Vertel fork. The OCA
    ``fsm.location`` model does not exist here; its two responsibilities
    are split:

    * the **elevator** is ``maintenance.equipment`` (``equipment_id``)
    * the **address** is the property, ``property.property``
      (``property_id``, computed from ``equipment_id.property_id``)

    Invoicing goes through ``partner_id`` (``res.partner``), which is a
    separate track from the address — the address tells a technician
    where to drive, the partner is who gets billed.
    """

    _inherit = 'fieldservice.order'

    # Active orders on the same equipment
    active_order_count = fields.Integer(
        string='Aktiva ordrar',
        compute='_compute_active_order_count',
    )

    # Reporter. The fork already has reporter, computed from
    # stakeholder_ids (the stakeholder with partner_status 'reporter'),
    # so it is read only and cannot be written. The phone is a related
    # read of the same partner rather than a second stored field.
    reporter_phone = fields.Char(
        string="Telefon",
        related='reporter.phone',
        readonly=True,
    )

    # Address — read from the property. Display only: the form and the
    # kanban card show it so a technician knows where to drive. Billing
    # is partner_id, a different track.
    street = fields.Char(related='property_id.street', readonly=True)
    city = fields.Char(related='property_id.city', readonly=True)

    # Type colour — the order type is reached through the product in this
    # fork (product_tmpl_id.product_type), not through a type field.
    type_color = fields.Char(
        related='product_tmpl_id.product_type.color',
        string="Type Color",
        readonly=True,
    )

    # Priority — 5 levels (replaces 4-level OCA default + star widget)
    priority = fields.Selection([
        ('0', 'Planerad'),
        ('1', 'Låg'),
        ('2', 'Normal'),
        ('3', 'Hög'),
        ('4', 'Kritisk'),
    ], string='Prioritet', default='2', tracking=True, index=True)

    TYPE_PRIORITY_MAP = {
        'fieldservice_order_type_color.fsm_order_type_service': '1',
        'fieldservice_order_type_color.fsm_order_type_repair': '2',
        'fieldservice_order_type_color.fsm_order_type_troubleshooting': '3',
        'fieldservice_order_type_color.fsm_order_type_inspection': '2',
        'fieldservice_order_type_color.fsm_order_type_inspection_remark': '3',
        'fieldservice_order_type_color.fsm_order_type_inspection_remark_red': '4',
        'fieldservice_order_type_color.fsm_order_type_new_installation': '0',
        'fieldservice_order_type_color.fsm_order_type_modernization': '0',
        'fieldservice_order_type_color.fsm_order_type_upgrade': '0',
    }
    RED_REMARK_TYPE_XMLID = (
        'fieldservice_order_type_color.fsm_order_type_inspection_remark_red'
    )

    # Elevator operational status (related from equipment, read-only)
    location_operational_status = fields.Selection(
        related='equipment_id.operational_status',
        string='Hiss driftstatus',
        readonly=True,
        store=True,
    )
    location_operational_status_str = fields.Char(
        compute='_compute_location_operational_status_str',
        string='Hiss driftstatus (text)',
    )

    # Elevator data (related from equipment, read-only)
    elevator_type_id = fields.Many2one(related='equipment_id.elevator_type_id', readonly=True)
    manufacturing_number = fields.Char(related='equipment_id.manufacturing_number', readonly=True)
    control_system_id = fields.Many2one(related='equipment_id.control_system_id', readonly=True)
    mechanical_brand_id = fields.Many2one(related='equipment_id.mechanical_brand_id', readonly=True)
    car_door_type_id = fields.Many2one(related='equipment_id.car_door_type_id', readonly=True)
    shaft_door_type_id = fields.Many2one(related='equipment_id.shaft_door_type_id', readonly=True)
    lubrication_type_id = fields.Many2one(related='equipment_id.lubrication_type_id', readonly=True)
    bearing_config_id = fields.Many2one(related='equipment_id.bearing_config_id', readonly=True)

    # Emergency phone (related from equipment)
    emergency_phone_type_id = fields.Many2one(related='equipment_id.emergency_phone_type_id', readonly=True)
    gsm_device_id = fields.Many2one(related='equipment_id.gsm_device_id', readonly=True)
    p100 = fields.Char(related='equipment_id.p100', readonly=True)
    sim_image = fields.Binary(related='equipment_id.sim_image', readonly=True)

    # Inspection (related from equipment)
    last_inspection = fields.Date(related='equipment_id.last_inspection', readonly=True)
    inspection_company_id = fields.Many2one(related='equipment_id.inspection_company_id', readonly=True)
    inspection_number = fields.Char(related='equipment_id.inspection_number', readonly=True)
    inspection_month = fields.Selection(related='equipment_id.inspection_month', readonly=True)

    # Images
    location_image_ids = fields.Many2many(
        'ir.attachment',
        'fsm_order_attachment_rel',
        'order_id',
        'attachment_id',
        string="Pictures",
    )

    @api.depends('location_operational_status')
    def _compute_location_operational_status_str(self):
        status_map = dict(
            self.env['maintenance.equipment']._fields['operational_status'].selection)
        for order in self:
            order.location_operational_status_str = status_map.get(
                order.location_operational_status, '')

    @api.onchange('equipment_id')
    def _onchange_equipment_id_person(self):
        """Pre-fill the technician from the equipment's default technician."""
        if self.equipment_id and self.equipment_id.technician_user_id:
            employee = self.env['hr.employee'].search(
                [('user_id', '=', self.equipment_id.technician_user_id.id)],
                limit=1,
            )
            if employee:
                self.requested_employee_ids = [(6, 0, employee.ids)]

    @api.onchange('product_tmpl_id')
    def _onchange_type_priority(self):
        if self.product_tmpl_id.product_type:
            self.priority = self._priority_for_type(
                self.product_tmpl_id.product_type) or '2'

    def _priority_for_type(self, order_type):
        if not order_type:
            return False
        xmlid = order_type.get_external_id().get(order_type.id, '')
        return self.TYPE_PRIORITY_MAP.get(xmlid)

    def _type_xmlid(self, type_id):
        if not type_id:
            return ''
        return self.env['fieldservice.order.type'].browse(
            type_id).get_external_id().get(type_id, '')

    def _maybe_shutdown_red_remark(self):
        """Red inspection remark -> elevator must be taken out of service."""
        for order in self:
            if not order.equipment_id:
                continue
            order_type = order.product_tmpl_id.product_type
            if not order_type:
                continue
            xmlid = order_type.get_external_id().get(order_type.id, '')
            if (xmlid == self.RED_REMARK_TYPE_XMLID
                    and order.equipment_id.operational_status == 'operational'):
                order.equipment_id.write({
                    'operational_status': 'out_of_order',
                    'out_of_order_reason': 'Röd besiktningsanmärkning',
                    'out_of_order_date': fields.Date.context_today(self),
                })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('product_tmpl_id') and 'priority' not in vals:
                tmpl = self.env['product.template'].browse(
                    vals['product_tmpl_id'])
                vals['priority'] = self._priority_for_type(
                    tmpl.product_type) or '2'
        orders = super().create(vals_list)
        orders._auto_assign_stage()
        orders._maybe_shutdown_red_remark()
        return orders

    def write(self, vals):
        if vals.get('product_tmpl_id') and 'priority' not in vals:
            tmpl = self.env['product.template'].browse(vals['product_tmpl_id'])
            vals['priority'] = self._priority_for_type(tmpl.product_type) or '2'
        res = super().write(vals)
        if (vals.get('requested_employee_ids') or vals.get('equipment_id')
                or vals.get('planned_start_datetime')):
            self._auto_assign_stage()
        if 'product_tmpl_id' in vals:
            self._maybe_shutdown_red_remark()
        return res

    def _default_stage_id(self):
        """The stage an order starts in: the first open one by sequence.

        The fork has no _default_stage_id of its own, so it is derived from
        fieldservice.stage rather than hard-coded.
        """
        return self.env['fieldservice.stage'].search(
            [('is_closed', '=', False)], order='sequence', limit=1
        )

    def _auto_assign_stage(self):
        new_stage = self._default_stage_id()
        assigned_stage = self.env.ref(
            'fieldservice_vrtl.fieldservice_stage_assigned', raise_if_not_found=False
        )
        scheduled_stage = self.env.ref(
            'fieldservice_vrtl.fieldservice_stage_planning', raise_if_not_found=False
        )
        for order in self:
            if order.stage_id != new_stage:
                continue
            if order.planned_start_datetime and scheduled_stage:
                order.stage_id = scheduled_stage
            elif order.requested_employee_ids and assigned_stage:
                order.stage_id = assigned_stage

    @api.depends('equipment_id')
    def _compute_active_order_count(self):
        for order in self:
            if order.equipment_id:
                order.active_order_count = self.search_count([
                    ('equipment_id', '=', order.equipment_id.id),
                    ('stage_id.is_closed', '=', False),
                ])
            else:
                order.active_order_count = 0

    def action_view_active_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Aktiva ordrar — %s') % self.equipment_id.name,
            'res_model': 'fieldservice.order',
            'view_mode': 'list,form',
            'domain': [
                ('equipment_id', '=', self.equipment_id.id),
                ('stage_id.is_closed', '=', False),
            ],
            'context': {'default_equipment_id': self.equipment_id.id},
        }

    def action_open_shutdown_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Registrera avstängning'),
            'res_model': 'elevata.elevator.shutdown.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_equipment_id': self.equipment_id.id},
        }

    def action_set_location_operational(self):
        self.ensure_one()
        self.equipment_id.write({
            'operational_status': 'operational',
            'out_of_order_reason': False,
        })
        return True

    # ── Stage transition actions ────────────────────────────────────────

    def _stage(self, xmlid):
        return self.env.ref(xmlid, raise_if_not_found=False)

    def action_assign(self):
        for order in self:
            if not order.requested_employee_ids:
                raise ValidationError(
                    _("Cannot move to Assigned until 'Assigned To' is filled in")
                )
        stage = self._stage('fieldservice_vrtl.fieldservice_stage_assigned')
        if not stage:
            return False
        return self.write({'stage_id': stage.id})

    def action_schedule(self):
        for order in self:
            if not order.planned_start_datetime:
                raise ValidationError(
                    _("Cannot move to Planning until a planned start is set")
                )
        stage = self._stage('fieldservice_vrtl.fieldservice_stage_planning')
        if not stage:
            return False
        return self.write({'stage_id': stage.id})

    def action_start(self):
        stage = self._stage('fieldservice_vrtl.fieldservice_stage_ongoing')
        if not stage:
            return False
        return self.write({'stage_id': stage.id})

    def action_complete(self):
        stage = self._stage('fieldservice_vrtl.fieldservice_stage_completed')
        if not stage:
            return False
        return self.write({'stage_id': stage.id})

    def action_cancel(self):
        stage = self._stage('fieldservice_vrtl.fieldservice_stage_cancelled')
        if not stage:
            return False
        return self.write({'stage_id': stage.id})
