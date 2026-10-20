import logging
from datetime import date

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    vacation_allocation_id = fields.Many2one(
        'hr.leave.allocation',
        string='Vacation Allocation',
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.contract') or _('New')
        records = super().create(vals_list)
        for contract in records:
            if contract.state == 'open':
                contract._sync_vacation_allocation()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals and vals['state'] == 'open':
            for contract in self:
                contract._sync_vacation_allocation()
        elif 'vacation_days' in vals:
            for contract in self.filtered(lambda c: c.state == 'open'):
                contract._sync_vacation_allocation()
        return res

    def _sync_vacation_allocation(self):
        leave_type = self.env.ref(
            'elevata_hr_contract.leave_type_semester', raise_if_not_found=False)
        if not leave_type:
            _logger.warning('Leave type "Semester" is missing — cannot create allocation.')
            return

        for contract in self:
            if not contract.employee_id or not contract.vacation_days:
                continue

            year = date.today().year
            date_from = date(year, 1, 1)
            date_to = date(year, 12, 31)

            if contract.vacation_allocation_id:
                contract.vacation_allocation_id.sudo().write({
                    'number_of_days': contract.vacation_days,
                })
                _logger.info(
                    'Updated vacation allocation %s -> %s days for %s',
                    contract.vacation_allocation_id.display_name,
                    contract.vacation_days,
                    contract.employee_id.name,
                )
            else:
                allocation = self.env['hr.leave.allocation'].sudo().create({
                    'holiday_status_id': leave_type.id,
                    'employee_id': contract.employee_id.id,
                    'number_of_days': contract.vacation_days,
                    'holiday_type': 'employee',
                    'allocation_type': 'regular',
                    'date_from': date_from,
                    'date_to': date_to,
                    'state': 'confirm',
                    'private_name': _('Vacation %s – %s') % (year, contract.name or ''),
                })
                try:
                    allocation.sudo().action_validate()
                except Exception:
                    _logger.warning(
                        'Kunde inte autovalidera semestertilldelning %s',
                        allocation.display_name,
                    )
                contract.vacation_allocation_id = allocation
                _logger.info(
                    'Created vacation allocation of %s days for %s',
                    contract.vacation_days,
                    contract.employee_id.name,
                )

    @api.model
    def _cron_yearly_vacation_allocation(self):
        """Create new vacation allocations for all active contracts at year end."""
        contracts = self.search([
            ('state', '=', 'open'),
            ('employee_id', '!=', False),
            ('vacation_days', '>', 0),
        ])
        year = date.today().year
        _logger.info(
            'Cron: created vacation allocations for %s, %d active contracts.',
            year, len(contracts),
        )
        for contract in contracts:
            # Check whether an allocation already exists for this year
            existing = contract.vacation_allocation_id
            if existing and existing.date_from and existing.date_from.year == year:
                continue  # Already created for this year
            # Reset the reference so _sync creates a new one
            contract.vacation_allocation_id = False
            contract._sync_vacation_allocation()

    # --- Collective agreement ---
    collective_agreement = fields.Selection([
        ('installationsavtalet', 'Installationsavtalet (EIO/SEF)'),
        ('tjanstemannaavtalet', 'Tjänstemannaavtalet (Unionen)'),
        ('teknikavtalet', 'Teknikavtalet (IF Metall)'),
        ('inget', 'No collective agreement'),
    ], string='Collective Agreement', tracking=True)

    # --- Notice period ---
    notice_period_employee = fields.Integer(
        string='Notice period, employee (months)',
        default=1,
        help='Notice period in months for the employee',
    )
    notice_period_employer = fields.Integer(
        string='Notice period, employer (months)',
        default=1,
        help='Notice period in months for the employer',
    )

    # --- Vacation ---
    vacation_days = fields.Integer(
        string='Vacation Days',
        default=25,
        help='Number of paid vacation days per year (statutory minimum: 25)',
    )

    # --- Employment percentage ---
    employment_percentage = fields.Float(
        string='Employment Percentage (%)',
        default=100.0,
        help='Share of full time in percent, e.g. 100 = full time, 80 = 80%',
    )

    # --- Work location ---
    work_location = fields.Selection([
        ('office', 'Company address'),
        ('home', 'Home based'),
        ('field', 'Field work'),
        ('hybrid', 'Hybrid'),
    ], string='Work Location', default='office', tracking=True)

    # --- Wage type ---
    wage_type = fields.Selection([
        ('monthly', 'Monthly salary'),
        ('hourly', 'Hourly wage'),
    ], string='Wage Type', default='monthly', tracking=True)

    # --- Pay frequency ---
    pay_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('biweekly', 'Every 14 days'),
        ('weekly', 'Weekly'),
    ], string='Pay Frequency', default='monthly')

    # --- Hourly wage ---
    hourly_wage = fields.Monetary(
        string='Hourly wage',
        help='Hourly wage in SEK (used when wage type is Hourly wage)',
    )

    # --- Computed: probation end date ---
    probation_end_date = fields.Date(
        string='Probation Until',
        help='End date of the probation period (max 6 months under LAS)',
    )

    # --- Buttons ---

    def action_activate_contract(self):
        """Activate the contract (draft -> open)."""
        for contract in self:
            if contract.state == 'draft':
                contract.state = 'open'

    def action_print_contract(self):
        """Print or download the contract PDF."""
        return self.env.ref(
            'elevata_hr_contract.action_report_hr_contract'
        ).report_action(self)

    def action_send_contract(self):
        """Open the mail composer with the contract PDF attached."""
        self.ensure_one()
        template = self.env.ref(
            'elevata_hr_contract.email_template_contract',
            raise_if_not_found=False,
        )
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        ctx = {
            'default_model': 'hr.contract',
            'default_res_ids': self.ids,
            'default_use_template': bool(template),
            'default_template_id': template.id if template else False,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send Employment Contract'),
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'views': [(compose_form.id, 'form')],
            'target': 'new',
            'context': ctx,
        }
