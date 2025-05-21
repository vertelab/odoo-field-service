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
            
            brands = [
                "Electrolux",
                "Bosch",
                "Samsung",
                "LG",
                "Miele",
                "Whirlpool",
                "Siemens",
                "AEG",
                "Philips",
                "Panasonic",
                "Gorenje",
                "Candy",
                "Zanussi",
                "Beko",
                "Smeg",
                "Grundig",
                "Sharp",
                "Hoover",
                "Hisense",
                "Indesit"
            ]

            models = [
                "EWF12853",
                "SMU68TS06S",
                "WW90T986ASH",
                "F4WV909P2E",
                "W1 Classic WDB030",
                "W8 W046WR SE",
                "iQ700 HB578A0S6S",
                "L7FBE843E",
                "EP5365",
                "NN-CS89L",
                "NRK6192MX",
                "CDPN 4D620PW",
                "ZDT26020FA",
                "WTL10410",
                "BLF01CREU",
                "GNFP3440X",
                "SJ-BA05DMXWF-EU",
                "DWOA413AHC3",
                "RB400N4BC3",
                "DIF 04B1"
            ]

            field_service_titles = [
                "Diskmaskin vägrar starta",
                "Kylskåp håller inte temperaturen",
                "Vattenläcka under tvättmaskin",
                "Ugn når inte rätt temperatur",
                "Torktumlaren slutar mitt i program",
                "Frysen isar igen snabbt",
                "Induktionshäll blir ojämnt varm",
                "Mikrovågsugn gnistrar vid användning",
                "Köksfläkt bullrar högt",
                "Diskmaskin visar felkod E17",
                "Tvättmaskin centrifugerar inte",
                "Kylskåp brummar konstant",
                "Ugn visar felkod F241",
                "Touchpanel på spishäll svarar inte",
                "Torktumlare stängs av slumpmässigt",
                "Kaffemaskin startar men brygger inte",
                "Vattenkokare slår inte av",
                "Matberedare startar inte",
                "Ismaskin producerar ingen is",
                "Ugn låst i demoläge"
            ]

            descriptions = [
                "Diskmaskinen reagerar inte när man försöker starta ett program. Ingen ljudsignal eller lysdiod visas.",
                "Kylskåpet håller inte maten kall trots att den är inställd på 4°C. Matvaror riskerar att förstöras.",
                "En vattenpöl bildas under tvättmaskinen efter varje användning. Misstänkt läckage från slang eller trumma.",
                "Ugnen blir endast ljummen trots att den är inställd på 200°C. Oförmåga att tillaga mat korrekt.",
                "Torktumlaren stannar mitt i programmet och måste startas om manuellt. Oklart vad som orsakar felet.",
                "Frysen måste frostas av varje vecka. Isbildning sker snabbt och påverkar förvaringsutrymme.",
                "Värmen fördelas ojämnt över spishällen, vilket leder till ojämn matlagning.",
                "Mikrovågsugnen börjar spraka och visa ljusbågar när den används, vilket skapar rädsla för brandrisk.",
                "Fläkten låter mycket högt även på låg inställning. Ljudnivån gör den nästan oanvändbar.",
                "Diskmaskinen vägrar starta och visar E17, vilket enligt manualen indikerar ett vattenintagsproblem.",
                "Tvättmaskinen hoppar över centrifugeringsfasen och lämnar kläderna blöta efter avslutat program.",
                "Ett konstant brummande ljud hörs från kylskåpet, även när det inte är igång.",
                "Ugnen visar felkod F241 och reagerar inte på knapptryck. Går ej att använda överhuvudtaget.",
                "Touchkontrollerna på induktionshällen fungerar inte längre. Ingen reaktion vid tryck.",
                "Torktumlaren stängs av efter några minuter utan felmeddelande. Måste startas om flera gånger.",
                "Kaffemaskinen går igång men inget kaffe bryggs trots att vatten och kaffebönor finns.",
                "Vattenkokaren fortsätter koka även efter uppnådd temperatur. Risk för överhettning.",
                "Matberedaren startar inte alls trots att alla delar är korrekt monterade.",
                "Ismaskinen i kylskåpet fyller inte längre på med is. Ingen uppenbar blockering.",
                "Ugnens reglage är låsta i ett så kallat 'demoläge'. Ingen funktion är tillgänglig."
            ]


            
            created_orders = 0
            all_records = self.env['fieldservice.order'].search([('stage_id','=',6)]).ids
            _logger.warning(f"{all_records=}")
            #old_fieldservice = all_records.browse(random.choice(all_records))
            #for employee in employees:
            use_old_records = False
            if use_old_records:
                for i in range(self.number_of_records):  
                        old_fieldservice = self.env['fieldservice.order'].browse(random.choice(all_records))
                        demoname = random.choice(field_service_titles) 
                        self.env['fieldservice.order'].create({
                            #'name': f'Demo Work Order {created_orders + 1}',
                            'name':old_fieldservice.felbeskrivning[:25],
                            'priority': str(random.randint(0, 3)),
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
                        self.env['fieldservice.order'].create({
                            #'name': f'Demo Work Order {created_orders + 1}',
                            'name':random.choice(field_service_titles),
                            'priority': str(random.randint(0, 3)),
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
