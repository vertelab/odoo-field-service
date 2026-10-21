from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

ACCOUNT_STAGES = [
    ('draft', 'Draft'),
    ('review', 'Needs Review'),
    ('confirmed', 'Confirmed'),
    ('invoiced', 'Fully Invoiced'),
    ('no', 'Nothing Invoiced'),
]


class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'

    contractor_cost_ids = fields.One2many(
        'fieldservice.order.cost', 'order_id', string="Contractor Costs"
    )
    employee_timesheet_ids = fields.One2many(
        'account.analytic.line', 'fsm_order_id', string="Employee Timesheets"
    )
    employee = fields.Boolean(
        compute='_compute_employee', store=True,
        help="True when at least one requested employee is linked to a user.",
    )
    total_cost = fields.Float(
        compute='_compute_total_cost',
        string="Total Cost",
        store=True,
        help="Employee time at hourly cost plus contractor costs.",
    )
    contractor_total = fields.Float(
        compute='_compute_contractor_cost',
        string="Contractor Cost Estimate",
        store=True,
    )
    employee_time_total = fields.Float(
        compute='_compute_employee_hours',
        string="Total Employee Hours",
        store=True,
    )
    bill_to = fields.Selection(
        [('contact', 'Customer'),
         ('property', 'Property Owner')],
        string="Bill To", default='contact', required=True,
        help="Who receives the invoice. 'Property Owner' bills the first "
             "stakeholder of the lift's property instead of the reporter.",
    )
    account_stage = fields.Selection(
        ACCOUNT_STAGES, string="Accounting Stage", default='draft',
        copy=False, tracking=True,
    )

    # ── Computed fields ─────────────────────────────────────────────────

    @api.depends('requested_employee_ids.user_id')
    def _compute_employee(self):
        for order in self:
            order.employee = any(
                employee.user_id for employee in order.requested_employee_ids
            )

    @api.depends('employee_timesheet_ids.unit_amount',
                 'employee_timesheet_ids.employee_id.hourly_cost',
                 'contractor_cost_ids.quantity',
                 'contractor_cost_ids.price_unit')
    def _compute_total_cost(self):
        for order in self:
            total = 0.0
            for line in order.employee_timesheet_ids:
                rate = line.employee_id.hourly_cost or 0.0
                total += line.unit_amount * rate
            for cost in order.contractor_cost_ids:
                total += cost.price_unit * cost.quantity
            order.total_cost = total

    @api.depends('contractor_cost_ids.quantity',
                 'contractor_cost_ids.price_unit')
    def _compute_contractor_cost(self):
        for order in self:
            order.contractor_total = sum(
                cost.price_unit * cost.quantity
                for cost in order.contractor_cost_ids
            )

    @api.depends('employee_timesheet_ids.unit_amount')
    def _compute_employee_hours(self):
        for order in self:
            order.employee_time_total = sum(
                line.unit_amount for line in order.employee_timesheet_ids
            )

    # ── Stage transitions ───────────────────────────────────────────────

    def action_complete(self):
        res = super().action_complete()
        for order in self:
            if order.account_stage == 'draft':
                order.account_stage = 'review'
        return res

    def account_confirm(self):
        for order in self:
            if order.account_stage != 'review':
                raise ValidationError(
                    _("Order must be in 'Needs Review' stage to confirm.")
                )
            if not order.employee_timesheet_ids and not order.contractor_cost_ids:
                raise ValidationError(
                    _("Cannot confirm without timesheets or contractor costs.")
                )
            order.account_stage = 'confirmed'

    def account_no_invoice(self):
        for order in self:
            order.account_stage = 'no'

    # ── Invoice creation ────────────────────────────────────────────────

    def account_create_invoice(self):
        for order in self:
            if order.account_stage != 'confirmed':
                raise ValidationError(
                    _("Order must be in 'Confirmed' stage to create an "
                      "invoice.")
                )
            invoice = order._create_customer_invoice()
            if not invoice:
                raise ValidationError(
                    _("No invoice lines could be prepared for %s.")
                    % order.name
                )
            order.account_stage = 'invoiced'
            invoice.message_post(body=_(
                "This invoice was created from work order: "
                "<a href=# data-oe-model=fieldservice.order "
                "data-oe-id=%(id)s>%(name)s</a>",
                id=order.id, name=order.name,
            ))

    def _invoice_partner(self):
        """The partner to invoice.

        ``bill_to`` lets a lift owner be billed instead of the reporter.
        Without it we fall back to the order's partner.
        """
        self.ensure_one()
        if self.bill_to == 'property' and self.equipment_id.property_id:
            stakeholder = self.equipment_id.property_id.stakeholder_ids.filtered(
                lambda s: s.partner_id
            )[:1]
            if stakeholder:
                return stakeholder.partner_id
        return self.partner_id

    def _create_customer_invoice(self):
        self.ensure_one()
        partner = self._invoice_partner()
        if not partner:
            raise ValidationError(
                _("Order %s has no customer to invoice.") % self.name
            )

        journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.company.id),
            ('type', '=', 'sale'),
            ('active', '=', True),
        ], limit=1)
        fpos = partner.property_account_position_id

        lines = self._prepare_invoice_lines(fpos)
        if not lines:
            return self.env['account.move']

        return self.env['account.move'].create({
            'partner_id': partner.id,
            'move_type': 'out_invoice',
            'journal_id': journal.id or False,
            'fiscal_position_id': fpos.id or False,
            'fsm_order_ids': [(4, self.id)],
            'fsm_equipment_id': self.equipment_id.id or False,
            'company_id': self.env.company.id,
            'invoice_line_ids': lines,
        })

    def _prepare_invoice_lines(self, fpos):
        self.ensure_one()
        lines = []
        analytic = self.analytic_distribution or False

        def note(text):
            lines.append((0, 0, {
                'name': text,
                'display_type': 'line_note',
                'quantity': 0,
                'price_unit': 0,
            }))

        equipment = self.equipment_id
        if equipment:
            location_text = equipment.name
            property_ = equipment.property_id
            if property_:
                location_text += ", %s" % property_.name
                if property_.street:
                    location_text += ", %s" % property_.street
                if property_.city:
                    location_text += ", %s" % property_.city
            note(_("Location: %s") % location_text)

        order_info = _("Order Number: %s") % self.name
        if self.reporter:
            reporter_info = self.reporter.display_name
            if self.reporter_phone:
                reporter_info += ", %s" % self.reporter_phone
            order_info += " (%s: %s)" % (_("Reporter"), reporter_info)
        note(order_info)

        if self.description:
            note(_("Description: %s") % self.description)
        if self.resolution:
            note(_("Resolution: %s") % self.resolution)

        timesheet_product = self.env.ref(
            'elevata_fsm_account.field_service_regular_time',
            raise_if_not_found=False,
        )
        for line in self.employee_timesheet_ids:
            product = line.product_id or timesheet_product
            if not product:
                continue
            lines.append((0, 0, {
                'product_id': product.id,
                'quantity': line.unit_amount,
                'name': line.name or product.display_name,
                'price_unit': line.price_per_hour or 0.0,
                'analytic_distribution': analytic,
                'tax_ids': [(6, 0, product.taxes_id.ids)],
                'fsm_order_ids': [(4, self.id)],
            }))

        for cost in self.contractor_cost_ids:
            taxes = cost.product_id.taxes_id
            tax_ids = fpos.map_tax(taxes) if fpos else taxes
            lines.append((0, 0, {
                'product_id': cost.product_id.id,
                'quantity': cost.quantity,
                'name': cost.product_id.display_name,
                'price_unit': cost.price_unit,
                'analytic_distribution': analytic,
                'tax_ids': [(6, 0, tax_ids.ids)],
                'fsm_order_ids': [(4, self.id)],
            }))

        return lines

    # ── Vendor bill creation ────────────────────────────────────────────

    def create_bills(self):
        self.ensure_one()
        vals = self._prepare_vendor_bill()
        if not vals.get('invoice_line_ids'):
            raise ValidationError(
                _("Order %s has no contractor costs to bill.") % self.name
            )
        return self.env['account.move'].sudo().create(vals)

    def _prepare_vendor_bill(self):
        self.ensure_one()
        vendor = False
        for cost in self.contractor_cost_ids:
            if cost.partner_id:
                vendor = cost.partner_id
                break
        if not vendor:
            raise ValidationError(
                _("Set a vendor on at least one contractor cost line before "
                  "creating a bill.")
            )

        journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.company.id),
            ('type', '=', 'purchase'),
            ('active', '=', True),
        ], limit=1)
        fpos = vendor.property_account_position_id
        analytic = self.analytic_distribution or False

        lines = []
        for cost in self.contractor_cost_ids:
            template = cost.product_id.product_tmpl_id
            accounts = template._get_product_accounts()
            taxes = template.supplier_taxes_id
            tax_ids = fpos.map_tax(taxes) if fpos else taxes
            lines.append((0, 0, {
                'product_id': cost.product_id.id,
                'quantity': cost.quantity,
                'name': cost.product_id.display_name,
                'price_unit': cost.price_unit,
                'account_id': accounts['expense'].id,
                'tax_ids': [(6, 0, tax_ids.ids)],
                'analytic_distribution': analytic,
                'fsm_order_ids': [(4, self.id)],
            }))

        return {
            'partner_id': vendor.id,
            'move_type': 'in_invoice',
            'journal_id': journal.id or False,
            'fiscal_position_id': fpos.id or False,
            'fsm_order_ids': [(4, self.id)],
            'company_id': self.env.company.id,
            'invoice_line_ids': lines,
        }
