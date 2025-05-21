from odoo import api, fields, models
import logging
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)

class FieldServiceOrderSLA(models.Model):
    _name = 'fieldservice.order.sla'
    _description = 'Order SLA Link'

    order_id = fields.Many2one('fieldservice.order', string="Order", required=True, ondelete='cascade')
    sla_id = fields.Many2one('fieldservice.sla', string="SLA", required=True, ondelete='cascade')
    assigned_date = fields.Datetime(string="Assigned Date", compute="_compute_assigned_date", store=False)
    sla_end_date = fields.Datetime(string='SLA End Date')
    target_reached_date = fields.Datetime(string="Target Reached Date")
    # deadline = fields.Datetime(string="Target Reached Date", compute="_compute_duration_to_sla", store=True)

    duration_to_sla = fields.Float(
        string='Duration to SLA (hours)',
        compute='_compute_duration_to_sla',
        store=False
    )

    sla_breached = fields.Boolean(
    string="SLA Breached",
    compute='_compute_sla_breached',
    store=True,
    )

    @api.depends('order_id','sla_id')
    def set_deadline(self):
        for record in self:
            record.deadline = record.order_id.create_date + timedelta(hours=record.sla_id.time_within)

    @api.depends('duration_to_sla', 'sla_id.time_within')
    def _compute_sla_breached(self):
        for rec in self:
            if rec.sla_id.time_within and rec.duration_to_sla:
                rec.sla_breached = rec.duration_to_sla > rec.sla_id.time_within
            else:
                rec.sla_breached = False

    @api.depends('order_id.create_date', 'sla_end_date', 'sla_id.sla_time_type', 'sla_id.calendar_id')
    def _compute_duration_to_sla(self):
        for rec in self:
            _logger.warning(
                f"Order {rec.order_id.id}: sla_time_type={rec.sla_id.sla_time_type}, calendar_id={rec.sla_id.calendar_id.id if rec.sla_id.calendar_id else 'None'}"
            )
            if rec.order_id.create_date and rec.sla_end_date:
                if rec.sla_id.sla_time_type == 'all_hours':
                    rec.duration_to_sla = (rec.sla_end_date - rec.order_id.create_date).total_seconds() / 3600.0
                    _logger.warning(f"All hours: {rec.duration_to_sla}")
                elif rec.sla_id.sla_time_type == 'work_hours' and rec.sla_id.calendar_id:
                    rec.duration_to_sla = rec.sla_id.calendar_id.get_work_hours_count(
                        rec.order_id.create_date, rec.sla_end_date)
                    _logger.warning(f"Work hours: {rec.duration_to_sla}")
                else:
                    rec.duration_to_sla = (rec.sla_end_date - rec.order_id.create_date).total_seconds() / 3600.0
                    _logger.warning(f"Fallback all hours: {rec.duration_to_sla}")
            else:
                rec.duration_to_sla = 0.0

    @api.depends('order_id.create_date', 'sla_id.time_within', 'sla_id.sla_time_type', 'sla_id.calendar_id')
    def _compute_assigned_date(self):
        for rec in self:
            sla = rec.sla_id
            start = rec.order_id.create_date

            if not sla or not start or not sla.time_within:
                rec.assigned_date = False
                _logger.warning(f"[SKIPPED] Saknar data på Order {rec.order_id.display_name}")
                continue

            hours = sla.time_within
            sla_type = sla.sla_time_type
            calendar = sla.calendar_id

            _logger.warning(
                f"[SLA PLAN] Order {rec.order_id.display_name}: start={start}, hours={hours}, type={sla_type}, calendar={calendar.display_name if calendar else 'None'}"
            )

            if sla_type == 'all_hours' or not calendar:
                rec.assigned_date = start + timedelta(hours=hours)
                _logger.info(f"[ALL HOURS] Resultat: {rec.assigned_date}")
            elif sla_type == 'work_hours':
                rec.assigned_date = rec._simulate_work_hours_forward(start, hours, calendar)
                _logger.info(f"[WORK HOURS] Resultat: {rec.assigned_date}")


    def _simulate_work_hours_forward(self, start, target_hours, calendar):
        """
        Går framåt i tiden från start och summerar arbetstimmar enligt calendar
        tills target_hours uppnåtts. Returnerar slutdatum.
        """
        current = start
        hours_accumulated = 0.0
        step = timedelta(minutes=15)  
        safety_counter = 0
        max_steps = int((target_hours * 4) * 24)  

        while hours_accumulated < target_hours and safety_counter < max_steps:
            next_step = current + step
            work_hours = calendar.get_work_hours_count(current, next_step)

            hours_accumulated += work_hours
            current = next_step
            safety_counter += 1

        if safety_counter >= max_steps:
            _logger.warning(f"[SIMULATION ABORTED] Max steps reached, deadline approx: {current}")
        else:
            _logger.debug(f"[SIMULATED] Total hours={hours_accumulated}, result={current}")

        return current
