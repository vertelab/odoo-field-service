from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FSMOrder(models.Model):
    _inherit = 'fieldservice.order'

    planning_calendar_event_id = fields.Many2one(
        'calendar.event',
        string="Planning Calendar Event",
        ondelete='set null',
        copy=False,
    )
    planning_line_ids = fields.One2many(
        'elevata.fsm.planning', 'fsm_order_id',
        string="Planning Lines",
    )

    def _get_planning_calendar_tag(self):
        if self.requested_employee_ids:
            return self.env.ref(
                'elevata_base.calendar_tag_planned_booked',
                raise_if_not_found=False,
            )
        return self.env.ref(
            'elevata_base.calendar_tag_planned_unbooked',
            raise_if_not_found=False,
        )

    def _prepare_planning_event_vals(self):
        self.ensure_one()
        if not self.planned_start_datetime:
            return False
        location_name = self.equipment_id.name if self.equipment_id else ''
        name_parts = [p for p in [self.name, location_name] if p]
        event_name = ' — '.join(name_parts) or _('Planned Order')

        partner_ids = []
        if self.requested_employee_ids and self.requested_employee_ids.user_id and self.requested_employee_ids.user_id.partner_id:
            partner_ids.append(self.requested_employee_ids.user_id.partner_id.id)

        tag = self._get_planning_calendar_tag()
        categ_ids = [(6, 0, [tag.id])] if tag else [(5, 0, 0)]
        # planned_date_end does not exist in our fork; fall back to
        # date_end, then to the start so the event has zero length.
        stop = self.date_end or self.planned_start_datetime

        return {
            'name': event_name,
            'start': self.planned_start_datetime,
            'stop': stop,
            'partner_ids': [(6, 0, partner_ids)],
            'categ_ids': categ_ids,
            'description': _("Type: %s\nWork Order: %s") % (
                self.product_type.name if self.product_type else '',
                self.name or '',
            ),
        }

    def _sync_planning_to_calendar(self):
        for order in self:
            vals = order._prepare_planning_event_vals()
            if not vals:
                if order.planning_calendar_event_id:
                    order.planning_calendar_event_id.unlink()
                    order.planning_calendar_event_id = False
                continue
            if order.planning_calendar_event_id:
                order.planning_calendar_event_id.with_context(
                    no_calendar_sync_back=True
                ).write(vals)
            else:
                event = self.env['calendar.event'].with_context(
                    no_calendar_sync_back=True
                ).create(vals)
                order.planning_calendar_event_id = event.id

    def _update_timesheet_calendar_tags(self):
        for order in self:
            for ts in order.employee_timesheet_ids.filtered('calendar_event_id'):
                tag = ts._get_calendar_tag()
                if tag:
                    ts.calendar_event_id.with_context(
                        no_calendar_sync_back=True
                    ).write({'categ_ids': [(6, 0, [tag.id])]})

    def write(self, vals):
        res = super().write(vals)
        sync_fields = {
            'planned_start_datetime', 'date_end',
            'planned_duration', 'requested_employee_ids', 'equipment_id',
        }
        if sync_fields & set(vals.keys()):
            self.filtered('planned_start_datetime')._sync_planning_to_calendar()
        if 'stage_id' in vals:
            self._update_timesheet_calendar_tags()
        return res

    def action_complete(self):
        res = super().action_complete()
        self._update_timesheet_calendar_tags()
        return res

    # ── Invoice with rate_type prices (extends elevata_fsm_account) ──

    def _prepare_invoice_lines(self):
        self.ensure_one()
        lines = super()._prepare_invoice_lines()
        return lines

    def account_create_invoice(self):
        invoices = self.env['account.move']
        for order in self:
            if order.account_stage != 'confirmed':
                raise ValidationError(
                    _("Order must be in 'Confirmed' stage to create invoice.")
                )

            jrnl = self.env['account.journal'].search([
                ('company_id', '=', self.env.company.id),
                ('type', '=', 'sale'),
                ('active', '=', True),
            ], limit=1)

            if order.bill_to == 'contact' and order.customer_id:
                partner = order.customer_id
            else:
                partner = order.equipment_id.customer_id

            fpos = partner.property_account_position_id
            invoice_vals = {
                'partner_id': partner.id,
                'move_type': 'out_invoice',
                'journal_id': jrnl.id or False,
                'fiscal_position_id': fpos.id or False,
                'fsm_order_ids': [(4, order.id)],
                'company_id': order.env.company.id,
            }

            invoice_line_vals = []
            analytic = (
                {str(order.equipment_id.analytic_account_id.id): 100.0}
                if order.equipment_id and order.equipment_id.analytic_account_id
                else False
            )

            # Note lines
            if order.equipment_id:
                loc = order.equipment_id
                loc_text = loc.name
                if loc.street:
                    loc_text += ", %s" % loc.street
                if loc.city:
                    loc_text += ", %s" % loc.city
                invoice_line_vals.append((0, 0, {
                    'name': _("Location: %s") % loc_text,
                    'display_type': 'line_note',
                    'quantity': 0, 'price_unit': 0,
                }))

            order_info = _("Order: %s") % order.name
            if order.reporter:
                reporter_info = order.reporter
                if order.reporter_phone:
                    reporter_info += ", %s" % order.reporter_phone
                order_info += " (%s: %s)" % (_('Reporter'), reporter_info)
            invoice_line_vals.append((0, 0, {
                'name': order_info,
                'display_type': 'line_note',
                'quantity': 0, 'price_unit': 0,
            }))

            if order.description:
                invoice_line_vals.append((0, 0, {
                    'name': _("Description: %s") % order.description,
                    'display_type': 'line_note',
                    'quantity': 0, 'price_unit': 0,
                }))

            if order.resolution:
                invoice_line_vals.append((0, 0, {
                    'name': _("Resolution: %s") % order.resolution,
                    'display_type': 'line_note',
                    'quantity': 0, 'price_unit': 0,
                }))

            # Timesheet lines with rate_type pricing
            if order.employee_timesheet_ids:
                timesheet_product = order.env.ref(
                    'elevata_fsm_account.field_service_regular_time',
                    raise_if_not_found=False,
                )
                rate_labels = dict(
                    order.env['account.analytic.line']._fields['rate_type']
                    ._description_selection(order.env)
                )
                for ts in order.employee_timesheet_ids:
                    rate_label = rate_labels.get(ts.rate_type, ts.rate_type or '')
                    price = ts.price_per_hour or (
                        ts.employee_id.hourly_cost if ts.employee_id else 0.0
                    )
                    line_name = '%s — %s' % (
                        rate_label,
                        ts.name or (timesheet_product.name if timesheet_product else _('Work')),
                    )
                    line = {
                        'quantity': ts.unit_amount,
                        'name': line_name,
                        'price_unit': price,
                        'analytic_distribution': analytic,
                    }
                    if timesheet_product:
                        line['product_id'] = timesheet_product.id
                        line['tax_ids'] = [(6, 0, timesheet_product.taxes_id.ids)]
                    invoice_line_vals.append((0, 0, line))

            # Material lines
            for cost in order.contractor_cost_ids:
                template = cost.product_id.product_tmpl_id
                taxes = template.taxes_id
                tax_ids = fpos.map_tax(taxes) if fpos else taxes
                invoice_line_vals.append((0, 0, {
                    'product_id': cost.product_id.id,
                    'quantity': cost.quantity,
                    'price_unit': cost.price_unit,
                    'analytic_distribution': analytic,
                    'tax_ids': [(6, 0, tax_ids.ids)],
                }))

            invoice_vals['invoice_line_ids'] = invoice_line_vals
            if invoice_line_vals:
                invoice = self.env['account.move'].create(invoice_vals)
                invoices |= invoice
                order.write({'account_stage': 'invoiced'})
                body = _(
                    "Invoice created from work order: "
                    "<a href=# data-oe-model=fsm.order data-oe-id=%d>%s</a>"
                ) % (order.id, order.name)
                invoice.message_post(body=body)
                order.action_invoice()

        if invoices:
            action = self.env['ir.actions.actions']._for_xml_id(
                'account.action_move_out_invoice_type'
            )
            if len(invoices) == 1:
                action.update({
                    'res_id': invoices.id,
                    'view_mode': 'form',
                    'views': [(False, 'form')],
                })
            else:
                action['domain'] = [('id', 'in', invoices.ids)]
            return action
