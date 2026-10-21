from odoo import models, fields, api


class ElevataOfferTemplate(models.Model):
    _name = 'elevata.offer.template'
    _description = 'Elevata Offertmall'
    _order = 'sequence, id'

    name = fields.Char(string='Mallnamn', required=True)
    sequence = fields.Integer(default=10)
    offer_type = fields.Selection([
        ('serviceavtal', 'Serviceavtal'),
        ('reparation', 'Reparation / Uppgradering'),
        ('modernisering', 'Modernisering'),
        ('nyinstallation', 'Nyinstallation'),
    ], string='Offerttyp', required=True, default='reparation')
    active = fields.Boolean(default=True)
    warranty_years = fields.Selection([
        ('1', '1 år'),
        ('2', '2 år'),
        ('3', '3 år'),
        ('5', '5 år'),
    ], string='Garantitid', default='1')
    repair_payment_structure = fields.Selection([
        ('30net', '30 dagar netto'),
        ('15net', '15 dagar netto'),
        ('immediate', 'Omedelbar betalning'),
        ('thirds', '1/3 beställning, 1/3 materialleverans, 1/3 besiktning'),
        ('5050', '50% vid order, 50% vid färdigställt arbete'),
    ], string='Betalningsstruktur', default='30net')
    simple_layout = fields.Boolean(string='Enkel offert (1 sida)')
    # Uppdrag
    background = fields.Html(string='Bakgrund / Orsak', sanitize=True)
    scope_of_work = fields.Html(string='Arbetsbeskrivning', sanitize=True)
    estimated_days = fields.Integer(string='Uppskattad tid (arbetsdagar)')
    downtime_info = fields.Text(string='Driftstopp')
    # Villkor
    warranty_terms = fields.Html(string='Garantivillkor', sanitize=True)
    payment_terms_text = fields.Html(string='Betalningsvillkor (fritext)', sanitize=True)
    terms_conditions = fields.Html(string='Allmänna villkor', sanitize=True)
    delivery_time_info = fields.Char(string='Leveranstid (kort)')
    delivery_time = fields.Html(string='Leveranstid', sanitize=True)
    delivery_terms = fields.Html(string='Leveransvillkor', sanitize=True)
    not_included = fields.Html(string='Ingår ej', sanitize=True)
    # Modernisering
    modernization_proposal = fields.Html(string='Vårt förslag', sanitize=True)
    modernization_construction_time = fields.Char(string='Ombyggnadstid')
    modernization_inspection_note = fields.Html(string='Besiktning', sanitize=True)
    modernization_quality_env = fields.Html(string='Kvalitet och Miljö', sanitize=True)
    modernization_reservations = fields.Html(string='Förtydliganden & Reservationer', sanitize=True)
    # Teknisk beskrivning
    tech_general = fields.Html(string='Allmänt', sanitize=True)
    tech_doors = fields.Html(string='Automatdörrar schakt', sanitize=True)
    tech_machine_room = fields.Html(string='Maskinrum', sanitize=True)
    tech_shaft = fields.Html(string='Schakt', sanitize=True)
    tech_car = fields.Html(string='Hisskorg', sanitize=True)
    tech_control_panel = fields.Html(string='Apparatställ', sanitize=True)
    tech_signalization = fields.Html(string='Signalisering / Tablåer', sanitize=True)
    tech_options = fields.Html(string='Optioner', sanitize=True)
    # Serviceavtal
    content = fields.Html(string='Uppdragsbeskrivning', sanitize=True)
    billing_interval = fields.Selection([
        ('monthly', 'Månadsvis'),
        ('quarterly', 'Kvartalsvis'),
        ('yearly', 'Årsvis'),
        ('manual', 'Manuell'),
    ], string='Faktureringsintervall')
    contract_years = fields.Selection([
        ('1', '1 år'),
        ('2', '2 år'),
        ('3', '3 år'),
        ('4', '4 år'),
        ('5', '5 år'),
    ], string='Avtalsår')

    # Design
    cover_image = fields.Binary(string='Omslagsbild')
    cover_image_filename = fields.Char(string='Filnamn omslagsbild')
    accent_color = fields.Char(string='Accentfärg', default='#2F4560')
    footer_text = fields.Text(string='Egen sidfotstext')
    cover_feature_1 = fields.Char(string='Omslagspunkt 1')
    cover_feature_2 = fields.Char(string='Omslagspunkt 2')
    cover_feature_3 = fields.Char(string='Omslagspunkt 3')

    design_version = fields.Selection([
        ('legacy', 'Tidigare layout'), ('v6', 'V6')
    ], string='Layoutversion', default='legacy', required=True)
    offer_title = fields.Char(string='Offertrubrik')
    service_sections = fields.Html(string='Serviceinnehåll', sanitize=True)
    ce_compliance_note = fields.Text(string='CE / myndighetskrav')
    closing_title = fields.Char(string='Avslutningsrubrik', default='Tack för ert förtroende')
    closing_text = fields.Html(
        string='Avslutningstext', sanitize=True,
        default='<p>Vi ser fram emot ett gott samarbete kring er hiss.</p>'
                '<p>Har ni frågor eller vill diskutera omfattningen är ni varmt välkomna att kontakta oss.</p>',
    )

    line_ids = fields.One2many(
        'elevata.offer.template.line',
        'template_id',
        string='Mallrader',
        copy=True,
    )


class ElevataOfferTemplateLine(models.Model):
    _name = 'elevata.offer.template.line'
    _description = 'Elevata Offertmallrad'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'elevata.offer.template',
        string='Mall',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    line_type = fields.Selection([
        ('arbete', 'Arbete'),
        ('material', 'Material'),
        ('resa', 'Resa'),
        ('nodtelefon', 'Nödtelefon'),
        ('besiktning', 'Biträdande besiktning'),
        ('ovrigt', 'Övrigt'),
    ], string='Typ', required=True, default='arbete')
    rate_type = fields.Selection([
        ('normaltid', 'Normaltid (mån-fre 07:00-16:00)'),
        ('overtid_1_2h', 'Övertid 1-2 h'),
        ('overtid_2h_plus', 'Övertid efter 2 h'),
        ('lordag', 'Lördag'),
        ('sondag_helgdag', 'Söndag/Helgdag'),
        ('storhelg', 'Storhelg'),
        ('beredskap_vardag', 'Beredskap vardag'),
        ('beredskap_helg', 'Beredskap helg'),
        ('jourutryckning', 'Jourutryckning (min 3 h)'),
        ('restid', 'Restid'),
        ('servicebil_mil', 'Servicebil (kr/mil)'),
        ('servicebil_tid', 'Servicebil tid'),
        ('servicebil_fast', 'Servicebil fast avgift (kr)'),
        ('verktygsavgift', 'Verktygsavgift'),
    ], string='Tidtyp')
    product_id = fields.Many2one('product.product', string='Produkt')
    name = fields.Char(string='Beskrivning')
    quantity = fields.Float(string='Antal', default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Enhet')
    price_unit = fields.Float(string='À-pris', digits=(16, 2))
