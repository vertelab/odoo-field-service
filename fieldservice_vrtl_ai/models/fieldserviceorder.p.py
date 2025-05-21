from odoo import api, fields, models, _
from datetime import date 
from datetime import datetime, timedelta, time
import json
import logging
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'

    ai_quest_id = fields.Many2one(comodel_name='ai.quest',string="",help="")

    @api.depends("stage_id")
    def _onchange_stage_id(self):
        if self.stage_id.start_quest:
           self.start_quest()
        elif not self.stage_id.is_closed:
            if self.ai_quest_id:
                self.ai_quest_id.status = 'active'
                self.ai_quest_id.channel_id.write({'active': True,})
        else:
            if self.ai_quest_id.channel_id:
                self.ai_quest_id.status = 'done'
                self.ai_quest_id.channel_id.write({'active': False})

    @api.depends("name")
    def _onchange_name(self):
        if self.ai_quest_id:
            self.ai_quest_id.write({'name': f"{self.name}"})
            if self.ai_quest_id.channel_id:
                self.ai_quest_id.channel_id.write({'name': f"{self.name}"})


    @api.model_create_multi
    def create(self, vals):
        field_service_order_id = super(FieldServiceOrder, self).create(vals)
        if field_service_order_id.stage_id.start_quest:
           field_service_order_id.start_quest()
        return field_service_order_id

    def start_quest(self):
        for field_service_order_id in self:
            if not field_service_order_id.ai_quest_id:
                field_service_order_id.ai_quest_id = self.env['ai.quest'].create({
                    'name': f"{field_service_order_id.name}",
                    'ai_type': 'fieldservice-order',
                    'init_type': 'channel',
                    'status': 'active',
                    'description':'A quest to help a service tech in the field.',
                    'code': """result = quest.build(session=session,message=message_body).invoke(message_invoke)"""
                })
                self.env['ai.quest.agent'].create({
                    'ai_agent_id': self.env.ref('fieldservice_vrtl_ai.ai_agent_helpdesk_chat').id,
                    'ai_quest_id': field_service_order_id.ai_quest_id.id
                })
                field_service_order_id.ai_quest_id.channel_id = self.env['discuss.channel'].create({
                    'name': f"[{field_service_order_id.name}",
                    'ai_quest_id': field_service_order_id.ai_quest_id.id,
                    'description': _('Chat with fieldserviceorders'),
                })
                self.set_member_of_quest_chat()

    def set_member_of_quest_chat(self):
        for record in self:
            if record.ai_quest_id and record.ai_quest_id.channel_id:
               members = record.order_line_ids.fieldservice_order_line_employee_ids
               members.set_member_of_quest_chat()

    def write(self,vals):
          res = super(FieldServiceOrder, self).write(vals)
          if "name" in vals:
             self._onchange_name()
          if "stage_id" in vals:
             self._onchange_stage_id()
          return res

    
# Gonzo Examens


    def set_severity_level(self, severity_data):
        """
        Accepts either {"<id>": <severity>} or {"id": <id>, "severity": <value>}
        and maps 0/1/2 or 'low'/'medium'/'high' to field 'severity_level'.
        """
        severity_map = {
            0: "low",
            1: "medium",
            2: "high",
            "low": "low",
            "medium": "medium",
            "high": "high"
        }

        severity_value = None

        if isinstance(severity_data, dict):
            # Format: {"123": 2}
            if str(self.id) in severity_data:
                severity_value = severity_data[str(self.id)]
            elif self.id in severity_data:
                severity_value = severity_data[self.id]
            # Format: {"id": 123, "severity": 2}
            elif "id" in severity_data and "severity" in severity_data:
                if int(severity_data["id"]) == self.id:
                    severity_value = severity_data["severity"]

        mapped_value = severity_map.get(severity_value)

        if mapped_value:
            self.write({'severity_level': mapped_value})
        else:
            _logger.warning(f"Invalid severity value received: {severity_value}")


    def create_severity_question(self):
        brand = self.brand or "Unknown"
        model = self.model or "Unknown"
        serial = self.serial_number or "N/A"
        description = self.description or "No description"
        work_instructions = self.work_instructions or "None"
        record_id = self.id

        return (
            f"You will receive details about a service order.\n"
            f"- Brand: {brand}\n"
            f"- Model: {model}\n"
            f"- Serial Number: {serial}\n"
            f"- Description: {description}\n"
            f"- Work Instructions: {work_instructions}\n"
            f"- ID: {record_id}\n\n"
            f"Estimate how severe this case is. Use:\n"
            f"0 = low, 1 = medium, 2 = critical.\n"
            f"Respond ONLY in JSON format like this:\n"
            f'{{"{record_id}": 1}}'
        )


    def create_planning_data(self):
        context = self.build_planning_context()

        employee_ids = list(set(
            line.employee_id.id for line in self.order_line_ids if line.employee_id
        ))

        _logger.warning(f"[PLANNING] Employee IDs used: {employee_ids}")

        return {
            "order_id": context["order_id"],
            "duration_hours": context["duration_hours"],
            "sla_deadline": context["sla_deadline"],
            "employee_availability": context["employee_availability"],
            "employee_ids": employee_ids
        }

    def get_all_employees(self):
        employees = set()
        for order_line in self.order_line_ids:
            for line_emp in order_line.fieldservice_order_line_employee_ids:
                if line_emp.employee_id:
                    employees.add(line_emp.employee_id)
        return list(employees)

    def get_sla_deadline(self):
        deadlines = [
            sla.target_reached_date
            for sla in self.sla_ids
            if sla.target_reached_date
        ]
        return min(deadlines) if deadlines else None

    def get_all_employees(self):
        return self.env['hr.employee'].search([])

    # def get_employee_availability(self, employees, start_date):
    #     availability = {}
    #     for emp in employees:
    #         _logger.warning(f"Kontrollerar tillgänglighet för: {emp.name}")
    #         emp_avail = {}
    #         d = start_date
    #         work_days = 0

    #         calendar = emp.resource_calendar_id
    #         if not calendar:
    #             _logger.warning(f"{emp.name} har inget arbetsschema.")
    #             continue            

    #         while work_days < 5:
    #             if d.weekday() < 5:  
    #                 start_dt = datetime.combine(d, time.min)
    #                 end_dt = datetime.combine(d, time.max)

    #                 try:
    #                     worked_hours = self._prepare_employees_holiday_values(
    #                         employees=emp, date_from_tz=start_dt, date_to_tz=end_dt
                            
    #                     )
    #                     _logger.warning(f"It's the new logg _get_leave_days_data_batch!!!! {emp._get_leave_days_data_batch(start_dt, end_dt)}")
    #                     _logger.warning(f"It's the super new logg _get_work_days_data_batch!!!! {emp._get_work_days_data_batch(start_dt, end_dt)}")

    #                     _logger.warning(f"Kunde inte hämta arbetstid för {worked_hours}")
    #                     _logger.warning(f"dubbel kollar  {worked_hours}")
    #                 except Exception as e:
    #                     _logger.warning(f"------------------------------------------------------------- {emp.name} {d}: {e}")
    #                     worked_hours = 0.0

    #                 emp_avail[d] = worked_hours
    #                 _logger.warning(f"{emp.name} jobbar {worked_hours} timmar {d}")
    #                 work_days += 1
    #             _logger.warning(f"Kunde inte hämta arbetstid för  -------------------------------------------------------------{worked_hours}")
    #             d += timedelta(days=1)

    #         availability[emp.id] = emp_avail

    #     return availability

    def get_employee_availability(self, employees, start_date):
        """
        Returnerar ett dict med hur många timmar varje anställd redan har planerat per dag,
        måndag till fredag (5 arbetsdagar från start_date).
        Max 8 timmar per dag.
        """
        availability = {}

        for emp in employees:
            emp_avail = {}
            current_date = start_date
            days_added = 0

            while days_added < 5:
                if current_date.weekday() < 5:  
                    planned_lines = self.env['fieldservice.order.line'].search([
                        ('employee_id', '=', emp.id),
                        ('date_start', '>=', datetime.combine(current_date, time.min)),
                        ('date_start', '<=', datetime.combine(current_date, time.max))
                    ])

                    total_hours = sum(planned_lines.mapped('duration')) or 0.0
                    emp_avail[current_date] = min(total_hours, 8.0)

                    days_added += 1

                current_date += timedelta(days=1)

            availability[emp.id] = emp_avail

        return availability


    def get_all_employees(self):
        return self.env['hr.employee'].search([])
    
    def build_planning_context(self):
        sla_deadline = self.get_sla_deadline()

        employees = self.env['hr.employee'].search([])
        _logger.warning(f"[PLANNING] Employees found: {[e.id for e in employees]}")

        raw_availability = self.get_employee_availability(employees, date.today())

        duration = sum(self.order_line_ids.mapped("duration")) or 1.0
        _logger.warning(f"[PLANNING] Total duration to plan: {duration}h")

        availability = {}
        for emp in employees:
            emp_id = emp.id
            emp_avail = raw_availability.get(emp_id, {})
            availability[emp_id] = {
                d.isoformat(): round(hours, 2) for d, hours in emp_avail.items()
            }

        _logger.warning(f"[PLANNING] Availabilities: {availability}")

        return {
            "order_id": self.id,
            "sla_deadline": sla_deadline,
            "duration_hours": round(duration, 2),
            "employee_availability": availability,
            "valid_employee_ids": [emp.id for emp in employees],
        }



    def schedule_best_time_slot(self):
        ctx = self.build_planning_context()
        deadline = ctx["sla_deadline"]
        duration = ctx["duration_hours"]
        best_candidate = None
        best_day = None
        lowest_total = float('inf')

        for emp_id, days in ctx["employee_availability"].items():
            for day, hours in days.items():
                if deadline and day > deadline:
                    continue
                if hours + duration <= 9:
                    total = sum(days.values())
                    if total < lowest_total:
                        best_candidate = emp_id
                        best_day = day
                        lowest_total = total

        return {
            "employee_id": best_candidate,
            "scheduled_date": best_day.isoformat() if best_day else None
        }

    def create_planning_question(self):
        questions = []

        for order in self:
            ctx = order.build_planning_context()
            availability_json = json.dumps(ctx["employee_availability"], indent=2)

            question = (
                f"Order:{ctx['order_id']}\n"
                f"Duration:{ctx['duration_hours']}h\n"
                f"SLA:{ctx['sla_deadline'] or 'None'}\n"
                f"Availability:{availability_json}\n"
                f"Valid employee IDs: {order.line.employee_id}\n\n"
                f"Rules:\n"
                f"- Work 08:00–17:00 Mon–Fri\n"
                f"- Max 8h/employee/day\n"
                f"- Balance workload\n"
                f"- Never past SLA\n\n"
                f"Respond with JSON only:\n"
                f"{{\"{ctx['order_id']}\":{{\"start_date\":\"YYYY-MM-DD HH:MM:SS\",\"end_date\":\"YYYY-MM-DD HH:MM:SS\",\"employee_id\":<id from valid IDs>}}}}\n"
                f"Or: {{\"{ctx['order_id']}\":null}}"
            )

            questions.append(question)

        return questions


    def apply_ai_planning(self, planning_data):
        plan = planning_data.get(str(self.id))
        if not plan:
            _logger.warning(f"[AI PLANNING] No plan to apply for order {self.id}")
            return

        _logger.warning(f"[AI PLANNING] Apply plan to order {self.id}: {plan}")

        self.write({
            "planned_start_datetime": plan["start_date"],
            "deadline_datetime": plan["end_date"],
        })

        for line in self.order_line_ids:
            line_vals = {
                "employee_id": plan["employee_id"],
                "date_start": plan["start_date"],
                "date_end": plan["end_date"],
            }
            line.write(line_vals)

            _logger.warning(f"[AI PLANNING] Uppdaterade orderrad {line.id} med datum {plan['start_date']} – {plan['end_date']} och employee {plan['employee_id']}")

            if line.fieldservice_order_line_employee_ids:
                line.fieldservice_order_line_employee_ids[0].write({
                    'employee_id': plan["employee_id"]
                })
            else:
                self.env['fieldservice.order.line.employee'].create({
                    'fieldservice_order_line_id': line.id,
                    'employee_id': plan["employee_id"],
                    'description': 'Assigned by AI'
                })



    def build_quest_prompt(self):
        """
        Skapar fråga till AI-agenten baserat på orderns information.
        """
        ctx = self.build_planning_context()
        availability_json = json.dumps(ctx["employee_availability"], indent=2)

        question = (
            f"Order:{ctx['order_id']}\n"
            f"Duration:{ctx['duration_hours']}h\n"
            f"SLA:{ctx['sla_deadline'] or 'None'}\n"
            f"Availability:{availability_json}\n"
            f"Valid employee IDs: {ctx['valid_employee_ids']}\n\n"
            f"Rules:\n"
            f"- Work 08:00–17:00 Mon–Fri\n"
            f"- Max 8h/employee/day\n"
            f"- Balance workload\n"
            f"- Never past SLA\n\n"
            f"Respond with JSON only:\n"
            f'{{"{ctx["order_id"]}":{{"start_date":"YYYY-MM-DD HH:MM:SS","end_date":"YYYY-MM-DD HH:MM:SS","employee_id":<id from valid IDs>}}}}\n'
            f"Or: {{\"{ctx['order_id']}\":null}}"
        )

        return question
    

    def _prepare_employees_holiday_values(self, employees, date_from_tz, date_to_tz):
        self.ensure_one()

        work_days_data = employees._get_work_days_data_batch(date_from_tz, date_to_tz)
        return work_days_data
