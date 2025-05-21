from odoo import api, fields, models, _
from datetime import date as date_type
from datetime import datetime, timedelta
from odoo.tools import date_utils
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import logging
from odoo.exceptions import ValidationError
import json

_logger = logging.getLogger(__name__) 


class FieldServiceOrderLineEmployee(models.Model):
    _inherit = 'fieldservice.order.line.employee'
    
    def set_member_of_quest_chat(self):
        for line_employee in self:
            channel_id = False
            if line_employee.fieldservice_order_line_id and line_employee.fieldservice_order_line_id.order_id and line_employee.fieldservice_order_line_id.order_id.ai_quest_id:
               quest_id = line_employee.fieldservice_order_line_id.order_id.ai_quest_id
               if quest_id:
                  channel_id = quest_id.channel_id
            if line_employee.employee_id and line_employee.employee_id.user_id and channel_id:
               partner_id = line_employee.employee_id.user_id.partner_id
               already_partner = False
               for member in channel_id.channel_member_ids:
                   if partner_id == member.partner_id:
                      already_partner = True
                      break
               if not already_partner:
                  line_employee.env['discuss.channel.member'].create({'channel_id':channel_id.id,'partner_id':partner_id.id})

    @api.model_create_multi
    def create(self, vals):
        line_employee = super(FieldServiceOrderLineEmployee, self).create(vals)
        if line_employee.fieldservice_order_line_id and line_employee.fieldservice_order_line_id.order_id and line_employee.fieldservice_order_line_id.order_id.ai_quest_id:
           line_employee.set_member_of_quest_chat()
        return line_employee


    @api.model_create_multi
    def create(self, vals_list):
        # Create records in batch
        line_employees = super(FieldServiceOrderLineEmployee, self).create(vals_list)
        
        # Process each created record
        for line_employee in line_employees:
            if (line_employee.fieldservice_order_line_id and 
                line_employee.fieldservice_order_line_id.order_id and 
                line_employee.fieldservice_order_line_id.order_id.ai_quest_id):
                line_employee.set_member_of_quest_chat()
        
        return line_employees

    def write(self, vals):
        line_employee = super(FieldServiceOrderLineEmployee, self).write(vals)
        if 'employee_id' in vals:
           self.set_member_of_quest_chat()


    #GonzaloAI examen 

class FieldServiceOrderLine(models.Model):
    _inherit = 'fieldservice.order.line'
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Assigned Employee',
        help='Den anställda som tilldelats denna arbetsorder-rad.'
    )

    def set_duration(self, duration):
        
        if isinstance(duration, dict):
            duration_value = list(duration.values())[0]

            self.write({'duration': duration_value}) 
 
    def create_duration_question(self):
        order = self.order_id
        question = (
            f"Work description: {order.description or 'N/A'}.\n"
            f"Object Description: {order.brand or 'N/A'}.\n"
            f"Estimate the duration in hours to complete the task.\n"
            f"Return your result as JSON: {{\"{self.id}\": <duration_in_hours_float>}}"
        )
        return question
