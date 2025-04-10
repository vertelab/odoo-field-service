from odoo import api, fields, models, _
from datetime import datetime, timedelta
import random
import logging

_logger = logging.getLogger(__name__)

class CreateDemoDataWizard(models.TransientModel):
    _name = 'create.demo.data.wizard'
    _description = 'Create Demo Data Wizard'

    number_of_records = fields.Integer(string='Number of Records', default=10)

    @api.model
    def default_get(self, fields):
        res = super(CreateDemoDataWizard, self).default_get(fields)
        res['number_of_records'] = self.env['hr.employee'].search_count([]) * 5
        return res

    def action_create_demo_data(self):
        self.ensure_one()
        self = self.sudo()
        try:
            employees = self.env['hr.employee'].search([])
            
            brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD']
            models = ['Model1', 'Model2', 'Model3', 'Model4']
            descriptions = [
                'Network infrastructure upgrade',
                'Server maintenance',
                'Software installation',
                'Hardware replacement',
                'Security system update'
            ]

            field_service_titles = [
                   "Min diskmaskin startar inte",
                   "Kylskåpet kyler inte tillräckligt",
                   "Tvättmaskinen läcker vatten",
                   "Ugnen värms inte upp ordentligt",
                   "Torktumlaren torkar inte kläderna",
                   "Frysen frostar igen för snabbt",
                   "Spishällen värmer ojämnt",
                   "Mikrovågsugnen gnistrar när den används",
                   "Köksfläkten bullrar onormalt mycket",
                   "Diskmaskinen visar felkod E17",
                   "Tvättmaskinen centrifugerar inte",
                   "Kylskåpet avger konstiga ljud",
                   "Ugnen visar felkod F241",
                   "Induktionshällen reagerar inte på touch",
                   "Torktumlaren stängs av mitt i programmet",
                   "Kaffemaskinen brygger inte kaffe",
                   "Vattenkokaren stängs inte av automatiskt",
                   "Matberedaren startar inte",
                   "Ismaskinen i kylskåpet producerar inte is",
                   "Ugnen är fast i demoläge"
                   ] 

            
            created_orders = 0
            all_records = self.env['fieldservice.order'].search([('stage_id','=',6)]).ids
            _logger.warning(f"{all_records=}")
            #old_fieldservice = all_records.browse(random.choice(all_records))
            #for employee in employees:
            use_old_records = False
            if use_old_records:
                for i in range(self.number_of_records):  # Create 5 records per employee
                        old_fieldservice = self.env['fieldservice.order'].browse(random.choice(all_records))
                        planned_start = datetime(2025, 8, 11, 12, 0) + timedelta(days=created_orders)
                        planned_end = planned_start + timedelta(hours=2)
                        demoname = random.choice(field_service_titles) 
                        self.env['fieldservice.order'].create({
                            #'name': f'Demo Work Order {created_orders + 1}',
                            'name':old_fieldservice.felbeskrivning[:25],
                            'priority': str(random.randint(0, 3)),
                            'planned_start_datetime': planned_start,
                            'deadline_datetime': planned_end,
                            'planned_duration': 2,
                            'date_start': planned_start.date(),
                            'date_end': planned_start.date(),
                            'description': old_fieldservice.felbeskrivning,
                            'work_instructions': 'Inspect thoroughly and document findings',
                            'location_instructions': f'Location {random.randint(1, 50)}, Room {random.randint(1, 100)}',
                            'brand': old_fieldservice.fabrikat,
                            'model': old_fieldservice.modell,
                            'serial_number': old_fieldservice.serienr,
                            'product_number': old_fieldservice.produktnummer,
                            'marking': old_fieldservice.markning,
                            'purchase_date': fields.Date.today() - timedelta(days=random.randint(1, 1000)),
                        })
                        created_orders += 1
            else:
                for i in range(self.number_of_records):  # Create 5 records per employee
                        planned_start = datetime(2025, 8, 11, 12, 0) + timedelta(days=created_orders)
                        planned_end = planned_start + timedelta(hours=2)
                        self.env['fieldservice.order'].create({
                            #'name': f'Demo Work Order {created_orders + 1}',
                            'name':random.choice(field_service_titles),
                            'priority': str(random.randint(0, 3)),
                            'planned_start_datetime': planned_start,
                            'deadline_datetime': planned_end,
                            'planned_duration': 2,
                            'date_start': planned_start.date(),
                            'date_end': planned_start.date(),
                            'description': random.choice(descriptions),
                            'work_instructions': 'Inspect thoroughly and document findings',
                            'location_instructions': f'Location {random.randint(1, 50)}, Room {random.randint(1, 100)}',
                            'brand': random.choice(brands),
                            'model': random.choice(models),
                            'purchase_date': fields.Date.today() - timedelta(days=random.randint(1, 1000)),
                        })
                        created_orders += 1
                     
                            
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except Exception as e:
            raise e
            _logger.error(f"Error creating demo service orders: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('An error occurred while creating demo data.'),
                    'type': 'danger',
                }
            }
