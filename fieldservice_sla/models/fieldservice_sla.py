from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class FieldserviceSLA(models.Model):
    _name = 'fieldservice.sla'
    _description = 'Field Service SLA Module'

    name = fields.Char(string='SLA Schema', required=True)
    severity_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'Critic')
    ], string='Allvarlighetsgrad', required=True)
    order_sla_ids = fields.One2many('fieldservice.order.sla', 'sla_id', string="Order Links", ondelete='cascade')
    description = fields.Text(string='Description')
    time_within = fields.Float(string='Within')
    order_ids = fields.Many2many('fieldservice.order', string ="Tickets")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.company
    )
    stage_id = fields.Many2one(
        'fieldservice.stage',
        string='Target Stage',
        required=True,
        help="The stage that fulfills this SLA when the order reaches it."
    )
    sla_status = fields.Selection([
        ('on_track', 'On Track'),
        ('breached', 'Breached'),
    ], string="SLA Status", default='on_track')
    allowed_hours = fields.Float('Allowed Hours', required=True)
    sla_end_date = fields.Datetime(string='SLA End Date')

    # Aggregated fields for all linked orders
    avg_duration_to_sla = fields.Float(
        string='Avg Duration to SLA (hours)',
        compute='_compute_avg_duration_to_sla',
        store=False,
    )
    max_duration_to_sla = fields.Float(
        string='Max Duration to SLA (hours)',
        compute='_compute_avg_duration_to_sla',
        store=False,
    )
    min_duration_to_sla = fields.Float(
        string='Min Duration to SLA (hours)',
        compute='_compute_avg_duration_to_sla',
        store=False,
    )
    breached = fields.Boolean(
        string='Any SLA Breached',
        compute='_compute_breached',
        store=False,
    )
    sla_time_type = fields.Selection([
    ('all_hours', 'All Hours'),
    ('work_hours', 'Work Hours'),
    ], string='SLA Time Type')
    calendar_id = fields.Many2one('resource.calendar',string="Working Hours Calendar")


    @api.depends('order_sla_ids.duration_to_sla')
    def _compute_avg_duration_to_sla(self):
        for sla in self:
            durations = [link.duration_to_sla for link in sla.order_sla_ids if link.duration_to_sla]
            if durations:
                sla.avg_duration_to_sla = sum(durations) / len(durations)
                sla.max_duration_to_sla = max(durations)
                sla.min_duration_to_sla = min(durations)
            else:
                sla.avg_duration_to_sla = 0.0
                sla.max_duration_to_sla = 0.0
                sla.min_duration_to_sla = 0.0

    @api.depends('order_sla_ids.duration_to_sla', 'allowed_hours')
    def _compute_breached(self):
        for sla in self:
            sla.breached = any(
                link.duration_to_sla > sla.allowed_hours
                for link in sla.order_sla_ids if link.duration_to_sla and sla.allowed_hours
            )

    def set_stage_by_name(self, stage_name):
        stage = self.env['fieldservice.stage'].search([('name', '=', stage_name)], limit=1)
        if stage:
            self.stage_id = stage.id
        else:
            raise ValueError(_("Stage not found: %s") % stage_name)

    order_sla_count = fields.Integer(
        string="Number of Linked Orders",
        compute='_compute_order_sla_count'
    )

    def _compute_order_sla_count(self):
        for sla in self:
            sla.order_sla_count = len(sla.order_sla_ids)

    def action_view_linked_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Linked Orders'),
            'res_model': 'fieldservice.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.order_sla_ids.mapped('order_id').ids)],
            'context': dict(self.env.context, default_sla_id=self.id),
        }
