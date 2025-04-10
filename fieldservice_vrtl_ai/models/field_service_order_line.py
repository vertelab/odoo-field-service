from odoo import api, fields, models, _
from datetime import date as date_type
from datetime import datetime, timedelta
from odoo.tools import date_utils
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import logging 

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

    def set_duration(self, duration):
        
        if isinstance(duration, dict):
            duration_value = list(duration.values())[0]

            self.write({'duration': duration_value}) 
 
    def create_duration_question(self, records): 

        _logger.warning(f"{self=}") 
        questions =[] 
        order = self.order_id 

        for occasion in self: 
            order = occasion.order_id 
        question = f"Work description: {order.description}. Object Description is: {order.brand}" 
        _logger.warning(f"{question=}")  
        questions.append(question) 

        return questions 


    def allocate_employee(self, employee_dict):
        _logger.warning(f"{employee_dict=}")
        employee_id = int(list(employee_dict.keys())[0])
        if self.fieldservice_order_line_employee_ids:
            self.fieldservice_order_line_employee_ids[0].write({'employee_id':employee_id})
        else:
            self.env['fieldservice.order.line.employee'].create({'fieldservice_order_line_id':self.id,'employee_id':employee_id}) 


 

    @api.model  
    def calculate_employee_availability_depricated(self, records):  
        employee_time_list = []  
        employee_ids = self.env['hr.employee'].search([])  

        for order_line in records:  

            employee_time_dict = {}  

            if not order_line.fieldservice_order_line_employee_ids:  

                _logger.warning(f"{employee_ids=}")  

                for record in employee_ids:  

                    employee_time_dict[record.id] = [record.name, 0]  
                    already_planned_occasions = self.env['fieldservice.order.line'].search([  
                    ('fieldservice_order_line_employee_ids', '!=', False), 
                    ('fieldservice_order_line_employee_ids.employee_ids', '!=', False),  
                    ('date_start', '>=', order_line.date_start.replace(hour=0, minute=0, second=0)),  
                    ('date_start', '<', order_line.date_start.replace(hour=0, minute=0, second=0) + timedelta(days=1)) 
                    ])  
                    _logger.warning(f"{already_planned_occasions=}")  

                    for planned_occasion in already_planned_occasions: 

                        for employee in planned_occasion.fieldservice_order_line_employee_ids: 

                            employee_time_dict[employee.employee_id.id][1] += planned_occasion.duration 

                            _logger.warning(f"{employee=}") 
                            _logger.warning(f"{planned_occasion=}") 
                            _logger.warning(f"{planned_occasion.duration=}") 

                            employee_time_list.append(employee_time_dict)  

        return employee_time_list 
 
    @api.model  
    def calculate_employee_availability_day(self, date):  
        employee_time_dict = {}  
        
        _logger.warning(f"{employee_ids=}") # type: ignore 

        for record in employee_ids: # type: ignore 

            employee_time_dict[record.id] = [record.name, 0]  
            already_planned_occasions = self.env['fieldservice.order.line'].search([  
            ('fieldservice_order_line_employee_ids', '!=', False),  
            ('date_start', '>=', date.replace(hour=0, minute=0, second=0)),  
            ('date_start', '<', date.replace(hour=0, minute=0, second=0) + timedelta(days=1))  
            ])  

            _logger.warning(f"{already_planned_occasions=}")  

            for planned_occasion in already_planned_occasions:  

                for employee in planned_occasion.fieldservice_order_line_employee_ids:  

                    employee_time_dict[employee.employee_id.id] += planned_occasion.duration   

        return employee_time_dict 

    def analyze_employee_planning(self, records, session, quest): 
        grouped_records = records.read_group( 
        domain=[('id', 'in', records.ids)], 
        fields=['date_start', 'fieldservice_order_line_employee_ids'], 
        groupby=['date_start:day'] 
        ) 

 
    def get_least_planned_employee_question(self, records): 

        questions = [] 
        grouped_records = records.read_group( 
        domain=[('id', 'in', records.ids)], 
        fields=['date_start', 'fieldservice_order_line_employee_ids'], 
        groupby=['date_start:day'] 
        ) 

        for group in grouped_records: 

            date_str = group['date_start:day'] 
            modified_domain = group['__domain'].copy() 
            modified_domain.pop(0) 
            modified_domain.pop(0) 
            all_employees = self.env['hr.employee'].search([]) 
            employee_hours = {} 

            for employee in all_employees: 

                if True or employee.get_planned_hours(modified_domain) > 0: 

                    employee_hours[employee.id] = employee.get_planned_hours(modified_domain) 
                    question = f"On the day {date_str=}. Who is the least planned out of these? {employee_hours}" 
                    questions.append(question) 
                    _logger.warning(f"{question=}") 
                    
        return questions 
    