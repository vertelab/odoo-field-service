from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'

    order_sla_ids = fields.One2many('fieldservice.order.sla', 'order_id', string="SLAs", ondelete='cascade')

    fulfilled = fields.Boolean(string='Fulfilled', default=False)
    end_date = fields.Datetime(string='End Date')
    sla_ids = fields.Many2many('fieldservice.sla', string ="SLA")

    severity_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'Critic')
    ], string='Allvarlighetsgrad', required=True)

    sla_duration_hours = fields.Float(
        string='Duration to SLA (hours)',
        compute='_compute_duration_to_sla'
    )

    sla_breached = fields.Boolean(
        string='Any SLA Breached',
        compute='_compute_sla_breached',
    )

    # target_reached_duration = fields.Float(
    #     string="Target Reached Duration (hours)",
    #     compute='_set_target_reached_duration',
    # )

    @api.onchange('severity_level')
    def _onchange_severity_level(self):
        for order in self:
            order.order_sla_ids = [(5, 0, 0)]
            slas = self.env['fieldservice.sla'].search([('severity_level', '=', order.severity_level)])
            order.order_sla_ids = [
                (0, 0, {
                    'sla_id': sla.id,
                }) for sla in slas
            ]


    @api.depends('order_sla_ids.duration_to_sla')
    def _compute_sla_breached(self):
        for order in self:
            breached = False
            for order_sla in order.order_sla_ids:
                allowed = order_sla.sla_id.allowed_hours or 0
                if order_sla.duration_to_sla and order_sla.duration_to_sla > allowed:
                    breached = True
                    break
            order.sla_breached = breached

    @api.depends('order_sla_ids.sla_end_date', 'create_date')
    def _compute_duration_to_sla(self):
        for order in self:
            if order.order_sla_ids:
                order_sla = order.order_sla_ids[0]
                if order.create_date and order_sla.sla_end_date:
                    order.sla_duration_hours = (order_sla.sla_end_date - order.create_date).total_seconds() / 3600.0
                else:
                    order.sla_duration_hours = 0.0
            else:
                order.sla_duration_hours = 0.0

    reaction_time = fields.Float(string='Reaction Time', compute='_compute_reaktion_time', store=True, help='Time in hours')
    reaction_time_avg = fields.Float(string='Reaction Time (AVG)', group_operator='avg',
                                     compute='_compute_reaktion_time', store=True, help='Time in hours')
    reaction_time_min = fields.Float(string='Reaction Time (MIN)', group_operator='min',
                                     compute='_compute_reaktion_time', store=True, help='Time in hours')
    reaction_time_max = fields.Float(string='Reaction Time (MAX)', group_operator='max',
                                     compute='_compute_reaktion_time', store=True, help='Time in hours')
    time_until_work_start_avg = fields.Float(group_operator='avg', string='Resolution Time (AVG)',
                                             compute='_compute_time_until_work_start', store=True, help='Time in hours')
    time_until_work_start_max = fields.Float(group_operator="max", string='Resolution Time (MAX)',
                                             compute='_compute_time_until_work_start', store=True, help='Time in hours')
    time_until_work_start_min = fields.Float(group_operator="min", string='Resolution Time (MIN)',
                                             compute='_compute_time_until_work_start', store=True, help='Time in hours')

    time_until_work_done_avg = fields.Float(group_operator='avg', string='Arrival Time (AVG)',
                                            compute='_compute_time_until_work_done', store=True, help='Time in hours')
    time_until_work_done_min = fields.Float(group_operator='min', string='Arrival Time (MIN)',
                                            compute='_compute_time_until_work_done', store=True, help='Time in hours')
    time_until_work_done_max = fields.Float(group_operator='max', string='Arrival Time (MAX)',
                                            compute='_compute_time_until_work_done', store=True, help='Time in hours')

    time_until_work_start = fields.Float(string='Resolution Time', compute='_compute_time_until_work_start', store=True,
                                         help='Time in hours')
    time_until_work_done = fields.Float(string='Arrival Time', compute='_compute_time_until_work_done', store=True,
                                        help='Time in hours')



    @api.depends('create_date', 'date_start')
    def _compute_time_until_work_start(self):
        for record in self:
            if record.create_date and record.date_start:
                record.time_until_work_start = (record.date_start - record.create_date).total_seconds() / 3600
            else:
                record.time_until_work_start = 0.0
            record.time_until_work_start_avg = record.time_until_work_start
            record.time_until_work_start_min = record.time_until_work_start
            record.time_until_work_start_max = record.time_until_work_start

    @api.depends('date_start', 'date_end')
    def _compute_time_until_work_done(self):
        for record in self:
            if record.date_start and record.date_end:
                record.time_until_work_done = (record.date_end - record.date_start).total_seconds() / 3600
            else:
                record.time_until_work_done = 0.0
            record.time_until_work_done_avg = record.time_until_work_done
            record.time_until_work_done_max = record.time_until_work_done
            record.time_until_work_done_min = record.time_until_work_done

    @api.depends('create_date', 'planned_start_datetime')
    def _compute_reaktion_time(self):
        for record in self:
            if record.create_date and record.planned_start_datetime:
                record.reaction_time = (record.planned_start_datetime - record.create_date).total_seconds() / 3600
            else:
                record.reaction_time = 0.0
            record.reaction_time_avg = record.reaction_time
            record.reaction_time_min = record.reaction_time
            record.reaction_time_max = record.reaction_time

    def write(self, vals):
        _logger.warning(f"WRITE CALLED ON ORDER {self.ids} with vals: {vals}")
        res = super().write(vals)
        if 'stage_id' in vals:
            for order in self:
                _logger.warning(f"Order {order.id} stage_id is now {order.stage_id.id}")
                for order_sla in order.order_sla_ids:
                    _logger.warning(
                        f"Checking SLA {order_sla.id}: sla.stage_id={order_sla.sla_id.stage_id.id if order_sla.sla_id.stage_id else None}, "
                        f"order.stage_id={order.stage_id.id}, sla.sla_end_date={order_sla.sla_end_date}"
                    )
                    if order_sla.sla_id.stage_id and order_sla.sla_id.stage_id.id == order.stage_id.id and not order_sla.sla_end_date:
                        order_sla.write({'sla_end_date': fields.Datetime.now()})
                        _logger.warning(f"SLA end date set for SLA {order_sla.id} on order {order.id}")
        return res
