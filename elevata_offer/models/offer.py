import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


OFFER_TYPE = [
    ('serviceavtal', 'Serviceavtal'),
    ('reparation', 'Reparation / Uppgradering'),
    ('modernisering', 'Modernisering'),
    ('nyinstallation', 'Nyinstallation'),
]

OFFER_STATE = [
    ('draft', 'Utkast'),
    ('sent', 'Skickad'),
    ('negotiation', 'Förhandling'),
    ('won', 'Vunnen'),
    ('lost', 'Förlorad'),
    ('expired', 'Utgången'),
]


class ElevataOffer(models.Model):
    _name = 'elevata.offer'
    _description = 'Elevata Offert'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Offertnummer',
        default='New',
        readonly=True,
        copy=False,
        tracking=True,
    )
    offer_type = fields.Selection(
        OFFER_TYPE,
        string='Offerttyp',
        required=True,
        default='serviceavtal',
        tracking=True,
    )
    state = fields.Selection(
        OFFER_STATE,
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Kund',
        required=True,
        tracking=True,
    )
    date = fields.Date(
        string='Offertdatum',
        default=fields.Date.today,
        required=True,
    )
    validity_days = fields.Integer(
        string='Giltighetstid (dagar)',
        default=30,
    )
    validity_date = fields.Date(
        string='Giltig t.o.m.',
        compute='_compute_validity_date',
        store=True,
        tracking=True,
    )
    line_ids = fields.One2many(
        'elevata.offer.line',
        'offer_id',
        string='Offertrader',
        copy=True,
    )
    content = fields.Html(
        string='Offerttext',
        sanitize=True,
    )
    service_sections = fields.Html(
        string='Avtalets innehåll (sida 2)',
        sanitize=True,
        help='Redigerbart innehåll för sida 2 i serviceavtalsofferten — vad ingår i avtalet.',
    )
    amount_untaxed = fields.Float(
        string='Nettosumma',
        compute='_compute_amounts',
        store=True,
    )
    amount_total = fields.Float(
        string='Totalt inkl. moms',
        compute='_compute_amounts',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Ansvarig',
        default=lambda self: self.env.user,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Bolag',
        default=lambda self: self.env.company,
        required=True,
    )
    template_id = fields.Many2one(
        'elevata.offer.template',
        string='Använd mall',
        readonly=True,
        tracking=True,
    )
    lost_reason = fields.Char(string='Anledning till förlust')

    # ── Reparation / Uppgradering ──
    warranty_years = fields.Selection([
        ('1', '1 år'),
        ('2', '2 år'),
        ('3', '3 år'),
        ('5', '5 år'),
    ], string='Garantitid', default='1', tracking=True)
    repair_payment_structure = fields.Selection([
        ('30net', '30 dagar netto'),
        ('15net', '15 dagar netto'),
        ('immediate', 'Omedelbar betalning'),
        ('thirds', '1/3 beställning, 1/3 materialleverans, 1/3 besiktning'),
        ('5050', '50% vid order, 50% vid färdigställt arbete'),
    ], string='Betalningsstruktur', tracking=True, default='30net')
    delivery_time_info = fields.Char(
        string='Leveranstid',
        tracking=True,
        help='T.ex. "Ca 8 arbetsveckor från erhållen beställning"',
    )
    background = fields.Html(
        string='Bakgrund / Orsak',
        sanitize=True,
        help='Varför behövs reparationen? Felrapport, besiktningsanmärkning, slitage etc.',
    )
    scope_of_work = fields.Html(
        string='Arbetsbeskrivning',
        sanitize=True,
        help='Detaljerad teknisk specifikation av vad som ska utföras.',
    )
    estimated_days = fields.Integer(
        string='Uppskattad tid (arbetsdagar)',
    )
    estimated_start = fields.Selection([
        ('enligt_overenskommelse', 'Enligt överenskommelse'),
        ('1_vecka', 'Inom 1 vecka'),
        ('2_veckor', 'Inom 2 veckor'),
        ('1_manad', 'Inom 1 månad'),
        ('2_manader', 'Inom 2 månader'),
        ('3_manader', 'Inom 3 månader'),
    ], string='Planerad start', default='enligt_overenskommelse')
    downtime_info = fields.Text(
        string='Driftstopp',
        help='Förväntad påverkan på hissens tillgänglighet under arbetet.',
    )
    warranty_terms = fields.Html(
        string='Garantivillkor',
        sanitize=True,
    )
    terms_conditions = fields.Html(
        string='Allmänna villkor',
        sanitize=True,
    )
    payment_terms_text = fields.Html(
        string='Betalningsvillkor (fritext)',
        sanitize=True,
    )
    delivery_time = fields.Html(
        string='Leveranstid',
        sanitize=True,
    )
    delivery_terms = fields.Html(
        string='Leveransvillkor',
        sanitize=True,
    )
    not_included = fields.Html(
        string='Ingår ej',
        sanitize=True,
    )
    ce_compliance_note = fields.Text(
        string='CE / Myndighetskrav',
        help='CE-märkning eller andra myndighetskrav som gäller för uppdraget.',
    )

    # ── Modernisering ──
    modernization_proposal = fields.Html(
        string='Vårt förslag',
        sanitize=True,
        help='Övergripande lösningsbeskrivning för moderniseringen.',
    )
    modernization_construction_time = fields.Char(
        string='Ombyggnadstid',
        help='T.ex. "Ca 10 arbetsdagar / hiss"',
    )
    modernization_inspection_note = fields.Html(
        string='Besiktning',
        sanitize=True,
        help='Information om besiktningsansvar och myndighetskontakter.',
    )
    modernization_quality_env = fields.Html(
        string='Kvalitet och Miljö',
        sanitize=True,
    )
    modernization_reservations = fields.Html(
        string='Förtydliganden & Reservationer',
        sanitize=True,
    )
    # ── Teknisk beskrivning (modernisering) ──
    tech_general = fields.Html(
        string='Allmänt',
        sanitize=True,
        help='Kretsschema, instruktioner, skyltar etc.',
    )
    tech_doors = fields.Html(
        string='Automatdörrar schakt',
        sanitize=True,
    )
    tech_machine_room = fields.Html(
        string='Maskinrum',
        sanitize=True,
    )
    tech_shaft = fields.Html(
        string='Schakt',
        sanitize=True,
    )
    tech_car = fields.Html(
        string='Hisskorg',
        sanitize=True,
    )
    tech_control_panel = fields.Html(
        string='Apparatställ',
        sanitize=True,
    )
    tech_signalization = fields.Html(
        string='Signalisering / Tablåer',
        sanitize=True,
    )
    tech_options = fields.Html(
        string='Optioner',
        sanitize=True,
    )

    contract_start_date = fields.Date(
        string='Avtalsstartdatum',
        default=fields.Date.today,
        help='Startdatum för serviceavtalet. Synkas med offertdatum om ej åsidosätts manuellt.',
    )
    contract_years = fields.Selection([
        ('1', '1 år'),
        ('2', '2 år'),
        ('3', '3 år'),
        ('4', '4 år'),
        ('5', '5 år'),
    ], string='Avtalsår', default='1')
    billing_interval = fields.Selection([
        ('monthly', 'Månadsvis'),
        ('quarterly', 'Kvartalsvis'),
        ('yearly', 'Årsvis'),
        ('manual', 'Manuell'),
    ], string='Faktureringsintervall', default='yearly')
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Betalningsvillkor',
        default=lambda self: self.env.ref(
            'account.account_payment_term_30days', raise_if_not_found=False
        ),
        help='Betalningsvillkor som används på fakturan.',
    )

    version = fields.Integer(string='Version', default=1, readonly=True, copy=False)
    parent_id = fields.Many2one(
        'elevata.offer',
        string='Föregående version',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    version_ids = fields.One2many(
        'elevata.offer',
        'parent_id',
        string='Revisioner',
    )
    version_count = fields.Integer(
        string='Antal revisioner',
        compute='_compute_version_count',
    )

    service_contract_id = fields.Many2one(
        'elevata.service.contract',
        string='Serviceavtal',
        readonly=True,
        copy=False,
    )
    price_rule_ids = fields.One2many(
        'elevata.contract.price.rule',
        'offer_id',
        string='Prisregler',
        copy=True,
    )
    service_contract_count = fields.Integer(
        string='Antal serviceavtal',
        compute='_compute_service_contract_count',
    )
    fsm_order_ids = fields.Many2many(
        'fieldservice.order',
        string='Arbetsordrar',
        readonly=True,
        copy=False,
    )
    fsm_order_count = fields.Integer(
        string='Antal arbetsordrar',
        compute='_compute_fsm_order_count',
    )
    milestone_ids = fields.One2many(
        'elevata.offer.milestone',
        'offer_id',
        string='Betalningsplan',
        copy=False,
    )
    milestone_count = fields.Integer(
        string='Milstolpar',
        compute='_compute_milestone_count',
    )
    milestone_invoiced_pct = fields.Float(
        string='Fakturerat (%)',
        compute='_compute_milestone_count',
    )
    milestone_paid_pct = fields.Float(
        string='Betalt (%)',
        compute='_compute_milestone_count',
    )
    billing_state = fields.Selection([
        ('not_invoiced', 'Ej fakturerad'),
        ('partially_invoiced', 'Delvis fakturerad'),
        ('fully_invoiced', 'Slutfakturerad'),
        ('paid', 'Slutbetald'),
    ], string='Betalningsstatus', compute='_compute_milestone_count', store=True)

    @api.onchange('date')
    def _onchange_date_contract_start(self):
        if self.date:
            self.contract_start_date = self.date

    @api.depends('service_contract_id')
    def _compute_service_contract_count(self):
        for offer in self:
            offer.service_contract_count = 1 if offer.service_contract_id else 0

    @api.depends('version_ids')
    def _compute_version_count(self):
        for offer in self:
            offer.version_count = len(offer.version_ids)

    @api.depends('date', 'validity_days')
    def _compute_validity_date(self):
        for offer in self:
            if offer.date:
                offer.validity_date = offer.date + relativedelta(days=offer.validity_days or 0)
            else:
                offer.validity_date = False

    @api.depends('fsm_order_ids')
    def _compute_fsm_order_count(self):
        for offer in self:
            offer.fsm_order_count = len(offer.fsm_order_ids)

    @api.depends('milestone_ids', 'milestone_ids.state', 'milestone_ids.percentage')
    def _compute_milestone_count(self):
        for offer in self:
            milestones = offer.milestone_ids
            offer.milestone_count = len(milestones)
            invoiced = milestones.filtered(lambda m: m.state in ('invoiced', 'paid'))
            paid = milestones.filtered(lambda m: m.state == 'paid')
            offer.milestone_invoiced_pct = sum(invoiced.mapped('percentage'))
            offer.milestone_paid_pct = sum(paid.mapped('percentage'))
            if not milestones or offer.state != 'won':
                offer.billing_state = False
            elif all(m.state == 'paid' for m in milestones):
                offer.billing_state = 'paid'
            elif all(m.state in ('invoiced', 'paid') for m in milestones):
                offer.billing_state = 'fully_invoiced'
            elif any(m.state in ('invoiced', 'paid') for m in milestones):
                offer.billing_state = 'partially_invoiced'
            else:
                offer.billing_state = 'not_invoiced'

    report_html_url = fields.Char(compute='_compute_report_html_url')

    def get_report_html_content(self):
        self.ensure_one()
        html, _ = self.env['ir.actions.report']._render_qweb_html(
            'elevata_offer.report_offer_document', [self.id]
        )
        return html.decode('utf-8') if html else ''

    @api.depends('offer_type')
    def _compute_report_html_url(self):
        for rec in self:
            if rec.id:
                rec.report_html_url = f'/report/html/elevata_offer.report_offer_document/{rec.id}'
            else:
                rec.report_html_url = False

    @api.depends('line_ids.price_subtotal')
    def _compute_amounts(self):
        for offer in self:
            untaxed = sum(offer.line_ids.mapped('price_subtotal'))
            offer.amount_untaxed = untaxed
            offer.amount_total = untaxed * 1.25

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('content') and vals.get('offer_type'):
                vals['content'] = self._get_default_content_html(vals['offer_type'])
            if not vals.get('service_sections') and vals.get('offer_type') == 'serviceavtal':
                vals['service_sections'] = self._get_default_service_sections_html()
            if vals.get('offer_type') == 'reparation':
                if not vals.get('warranty_terms'):
                    vals['warranty_terms'] = (
                        '<p>Elevata garanterar utfört arbete i 12 månader och installerat '
                        'material i 24 månader från slutfört uppdrag. Garantin omfattar ej '
                        'slitage, felaktig användning eller åverkan.</p>'
                    )
                if not vals.get('terms_conditions'):
                    vals['terms_conditions'] = (
                        '<p>Offerten gäller det arbete som specificeras ovan. Tillkommande '
                        'arbete utförs efter separat överenskommelse. Eventuella '
                        'tilläggskostnader meddelas innan åtgärd vidtas.</p>'
                        '<p>Elevata ansvarar ej för förseningar orsakade av materialbrist, '
                        'force majeure eller omständigheter utanför vår kontroll.</p>'
                    )
                if not vals.get('payment_terms_text'):
                    vals['payment_terms_text'] = (
                        '<p>30 dagar netto. Vid uppdrag överstigande 50 000 kr: '
                        '50% vid beställning, 50% vid slutfört arbete.</p>'
                    )
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('elevata.offer') or 'New'
        return super().create(vals_list)

    def action_send(self):
        self.ensure_one()
        if self.state == 'draft':
            self.write({'state': 'sent'})
        elif self.state in ('sent', 'negotiation'):
            self._auto_save_version()
        pdf_content, _mime = self.env['ir.actions.report']._render_qweb_pdf(
            'elevata_offer.action_report_elevata_offer', res_ids=self.ids
        )
        attachment = self.env['ir.attachment'].create({
            'name': '%s.pdf' % self.name,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'elevata.offer',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        template = self.env.ref(
            'elevata_offer.email_template_elevata_offer',
            raise_if_not_found=False,
        )
        ctx = {
            'default_model': 'elevata.offer',
            'default_res_ids': self.ids,
            'default_composition_mode': 'comment',
            'force_email': True,
            'default_attachment_ids': [attachment.id],
        }
        if template:
            ctx['default_template_id'] = template.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Skicka offert'),
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }

    def action_negotiation(self):
        self.write({'state': 'negotiation'})

    def action_won(self):
        self.ensure_one()
        if (self.offer_type in ('reparation', 'modernisering', 'nyinstallation')
                and not self.line_ids.mapped('equipment_id')):
            raise UserError(_(
                'Välj hiss på minst en offertrad innan offerten markeras som '
                'vunnen. Arbetsordern behöver en hiss.'
            ))
        self.write({'state': 'won'})
        self._create_downstream_objects()
        self._save_contract_prices()
        if (self.offer_type == 'serviceavtal'
                and self.service_contract_id
                and self.billing_interval != 'manual'
                and self.service_contract_id.state == 'draft'
                and self.service_contract_id.line_ids):
            self.service_contract_id.action_confirm()
        if self.offer_type in ('reparation', 'modernisering', 'nyinstallation'):
            self._generate_milestones()
            first = self.milestone_ids.filtered(lambda m: m.state == 'pending')[:1]
            if first:
                self._create_milestone_invoice(first)

    def action_lost(self):
        self.write({'state': 'lost'})

    def action_expired(self):
        self.write({'state': 'expired'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    @api.model
    def _cron_check_expired(self):
        today = fields.Date.today()
        expired = self.search([
            ('state', 'in', ('sent', 'negotiation')),
            ('validity_date', '<', today),
        ])
        if expired:
            expired.write({'state': 'expired'})

    def _get_default_service_sections_html(self):
        return (
            '<p>Ett v&#228;lsk&#246;tt hissystem skapar trygghet i vardagen och minskar risken f&#246;r akuta driftstopp. '
            'Med serviceavtal fr&#229;n <strong>Elevata Hiss AB</strong> f&#229;r ni en strukturerad l&#246;sning '
            'f&#246;r hissens tillsyn och underh&#229;ll &#8212; med m&#228;nsklig kontakt och snabb respons n&#228;r det g&#228;ller.</p>'
            '<h4>Regelbundna servicebes&#246;k</h4>'
            '<p>Planerade bes&#246;k enligt ert avtals frekvens. V&#229;ra tekniker kontrollerar samtliga kritiska komponenter och dokumenterar statusen.</p>'
            '<ul>'
            '<li>Funktionskontroll av hissens huvudfunktioner</li>'
            '<li>Kontroll av d&#246;rrsystem och d&#246;rrmotor</li>'
            '<li>Kontroll av s&#228;kerhetskretsar</li>'
            '<li>Kontroll av maskin, broms och drivning</li>'
            '<li>Kontroll av linor, remmar och g&#229;ngbanor</li>'
            '</ul>'
            '<h4>F&#246;rebyggande &#229;tg&#228;rder och dokumentation</h4>'
            '<p>F&#246;rebyggande underh&#229;ll &#228;r alltid billigare &#228;n akuta reparationer. Vi sm&#246;rjer, justerar och dokumenterar varje bes&#246;k.</p>'
            '<ul>'
            '<li>Sm&#246;rjning, justering och &#229;tg&#228;rder</li>'
            '<li>Serviceprotokoll och digital dokumentation</li>'
            '<li>Rekommendationer vid uppt&#228;ckta brister</li>'
            '<li>Underlag f&#246;r framtida planering och budget</li>'
            '</ul>'
            '<h4>Snabb hj&#228;lp vid driftstopp</h4>'
            '<p>N&#228;r det uppst&#229;r ett fel vill ni ha hj&#228;lp direkt &#8212; inte i morgon. Vi prioriterar avtalskunderna och h&#229;ller er informerade.</p>'
            '<ul>'
            '<li>Jour med snabb insatstid</li>'
            '<li>Prioriterade servicetekniker</li>'
            '<li>Enkel felanm&#228;lan per telefon eller e-post</li>'
            '<li>Uppf&#246;ljning och &#229;terkoppling</li>'
            '</ul>'
        )

    def _get_default_content_html(self, offer_type):
        templates = {
            'serviceavtal': (
                '<p>Vi på Elevata tackar för förfrågan och lämnar härmed följande offert '
                'på serviceavtal.</p>'
                '<p>Offerten gäller de hissar som specificeras i offertraderna nedan.</p>'
                '<p>Vid frågor är du välkommen att kontakta oss.</p>'
            ),
            'reparation': (
                '<p>Vi på Elevata tackar för förfrågan och lämnar härmed följande offert '
                'på reparation/uppgradering.</p>'
                '<p>Arbetet utförs enligt specifikation i offertraderna nedan.</p>'
            ),
            'modernisering': (
                '<p>Vi på Elevata tackar för förfrågan och lämnar härmed följande offert '
                'på modernisering.</p>'
            ),
            'nyinstallation': (
                '<p>Vi på Elevata tackar för förfrågan och lämnar härmed följande offert '
                'på nyinstallation.</p>'
            ),
        }
        return templates.get(offer_type, '')

    @api.onchange('offer_type')
    def _onchange_offer_type_content(self):
        if self.offer_type and not self.content:
            self.content = self._get_default_content_html(self.offer_type)
        if self.offer_type == 'serviceavtal' and not self.service_sections:
            self.service_sections = self._get_default_service_sections_html()
        if self.offer_type == 'reparation':
            self._fill_repair_defaults()

    def _fill_repair_defaults(self):
        if not self.warranty_terms:
            self.warranty_terms = (
                '<p>Elevata garanterar utfört arbete i 12 månader och installerat '
                'material i 24 månader från slutfört uppdrag. Garantin omfattar ej '
                'slitage, felaktig användning eller åverkan.</p>'
            )
        if not self.terms_conditions:
            self.terms_conditions = (
                '<p>Offerten gäller det arbete som specificeras ovan. Tillkommande '
                'arbete utförs efter separat överenskommelse. Eventuella '
                'tilläggskostnader meddelas innan åtgärd vidtas.</p>'
                '<p>Elevata ansvarar ej för förseningar orsakade av materialbrist, '
                'force majeure eller omständigheter utanför vår kontroll.</p>'
            )
        if not self.payment_terms_text:
            self.payment_terms_text = (
                '<p>30 dagar netto. Vid uppdrag överstigande 50 000 kr: '
                '50% vid beställning, 50% vid slutfört arbete.</p>'
            )

    # ── Villkor-sync ──────────────────────────────────────────────
    WARRANTY_LABELS = {'1': '1 år', '2': '2 år', '3': '3 år', '5': '5 år'}

    def _build_villkor_vals(self):
        """Generera Villkor-HTML baserat på fältvärdena ovanför flikarna."""
        vals = {}
        if self.warranty_years:
            label = self.WARRANTY_LABELS.get(self.warranty_years, self.warranty_years)
            vals['warranty_terms'] = (
                '<p>Elevata garanterar utfört arbete i %s och installerat '
                'material i %s från slutfört uppdrag. Garantin omfattar ej '
                'slitage, felaktig användning eller åverkan.</p>'
            ) % (label, label)
        if self.repair_payment_structure:
            label = dict(self._fields['repair_payment_structure'].selection).get(
                self.repair_payment_structure, '')
            structure_details = {
                '30net': '<p>30 dagar netto.</p>',
                '15net': '<p>15 dagar netto.</p>',
                'immediate': '<p>Omedelbar betalning.</p>',
                'thirds': (
                    '<p>1/3 vid beställning, mot faktura, 30 dagar netto<br/>'
                    '1/3 vid materialleverans, mot faktura, 30 dagar netto<br/>'
                    '1/3 vid godkänd säkerhetsbesiktning, mot faktura, 30 dagar netto</p>'
                ),
                '5050': (
                    '<p>50% vid order, mot faktura, 30 dagar netto<br/>'
                    '50% vid färdigställt arbete, mot faktura, 30 dagar netto</p>'
                ),
            }
            vals['payment_terms_text'] = structure_details.get(
                self.repair_payment_structure, '<p>%s</p>' % label)
        if self.delivery_time_info:
            vals['delivery_time'] = '<p>%s</p>' % self.delivery_time_info
        return vals

    @api.onchange('warranty_years', 'repair_payment_structure', 'delivery_time_info')
    def _onchange_villkor_fields(self):
        if self.offer_type not in ('reparation', 'modernisering'):
            return
        for field, value in self._build_villkor_vals().items():
            setattr(self, field, value)

    def write(self, vals):
        res = super().write(vals)
        sync_map = {
            'warranty_years': 'warranty_terms',
            'repair_payment_structure': 'payment_terms_text',
            'delivery_time_info': 'delivery_time',
        }
        needs_sync = [
            k for k in sync_map
            if k in vals and sync_map[k] not in vals
        ]
        if needs_sync:
            for record in self.filtered(lambda r: r.offer_type in ('reparation', 'modernisering')):
                all_villkor = record._build_villkor_vals()
                update = {sync_map[k]: all_villkor[sync_map[k]]
                          for k in needs_sync if sync_map[k] in all_villkor}
                if update:
                    super(ElevataOffer, record).write(update)
        return res

    def action_insert_default_content(self):
        self.ensure_one()
        self.write({'content': self._get_default_content_html(self.offer_type)})

    def action_insert_default_service_sections(self):
        self.ensure_one()
        self.write({'service_sections': self._get_default_service_sections_html()})

    def action_load_template(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Välj offertmall'),
            'res_model': 'elevata.offer.template.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_offer_id': self.id},
        }

    def action_save_as_template(self):
        self.ensure_one()
        vals = {
            'name': '%s (från %s)' % (
                dict(self._fields['offer_type'].selection).get(self.offer_type, self.offer_type),
                self.name,
            ),
            'offer_type': self.offer_type,
        }
        # Kopiera alla mallfält
        for fname in (
            'warranty_years', 'repair_payment_structure', 'background',
            'scope_of_work', 'estimated_days', 'downtime_info',
            'warranty_terms', 'payment_terms_text', 'terms_conditions',
            'delivery_time_info', 'delivery_time', 'delivery_terms',
            'not_included', 'modernization_proposal',
            'modernization_construction_time', 'modernization_inspection_note',
            'modernization_quality_env', 'modernization_reservations',
            'tech_general', 'tech_doors', 'tech_machine_room', 'tech_shaft',
            'tech_car', 'tech_control_panel', 'tech_signalization',
            'tech_options', 'content', 'billing_interval', 'contract_years',
        ):
            val = getattr(self, fname, False)
            if val:
                vals[fname] = val
        if self.offer_type == 'reparation':
            vals['simple_layout'] = self.simple_layout
        # Design
        if self.cover_image:
            vals['cover_image'] = self.cover_image
        if self.accent_color and self.accent_color != '#2F4560':
            vals['accent_color'] = self.accent_color
        if self.footer_text:
            vals['footer_text'] = self.footer_text
        for cf in ('cover_feature_1', 'cover_feature_2', 'cover_feature_3'):
            val = getattr(self, cf, False)
            if val:
                vals[cf] = val
        for fname in (
            'design_version', 'offer_title', 'service_sections', 'ce_compliance_note',
            'closing_title', 'closing_text', 'cover_image_filename',
        ):
            vals[fname] = self[fname]
        template = self.env['elevata.offer.template'].create(vals)
        # Kopiera offertrader till mallrader
        for line in self.line_ids:
            self.env['elevata.offer.template.line'].create({
                'template_id': template.id,
                'sequence': line.sequence,
                'line_type': line.line_type,
                'rate_type': line.rate_type,
                'product_id': line.product_id.id if line.product_id else False,
                'name': line.name,
                'quantity': line.quantity,
                'uom_id': line.uom_id.id if line.uom_id else False,
                'price_unit': line.price_unit,
            })
        self.template_id = template.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sparad mall'),
            'res_model': 'elevata.offer.template',
            'view_mode': 'form',
            'res_id': template.id,
            'target': 'current',
        }

    def apply_template(self, template):
        self.ensure_one()
        vals = {'template_id': template.id, 'design_version': template.design_version}
        for fname in ('offer_title', 'service_sections', 'ce_compliance_note',
                      'closing_title', 'closing_text', 'cover_image_filename'):
            if template[fname] or template.design_version == 'v6':
                vals[fname] = template[fname]
        # Fält ovanför flikar
        if template.warranty_years:
            vals['warranty_years'] = template.warranty_years
        if template.repair_payment_structure:
            vals['repair_payment_structure'] = template.repair_payment_structure
        if template.offer_type == 'reparation':
            vals['simple_layout'] = template.simple_layout
        # Uppdrag
        if template.background:
            vals['background'] = template.background
        if template.scope_of_work:
            vals['scope_of_work'] = template.scope_of_work
        if template.estimated_days:
            vals['estimated_days'] = template.estimated_days
        if template.downtime_info:
            vals['downtime_info'] = template.downtime_info
        # Villkor
        if template.warranty_terms:
            vals['warranty_terms'] = template.warranty_terms
        if template.payment_terms_text:
            vals['payment_terms_text'] = template.payment_terms_text
        if template.terms_conditions:
            vals['terms_conditions'] = template.terms_conditions
        if template.delivery_time_info:
            vals['delivery_time_info'] = template.delivery_time_info
        if template.delivery_time:
            vals['delivery_time'] = template.delivery_time
        if template.delivery_terms:
            vals['delivery_terms'] = template.delivery_terms
        if template.not_included:
            vals['not_included'] = template.not_included
        # Modernisering
        if template.modernization_proposal:
            vals['modernization_proposal'] = template.modernization_proposal
        if template.modernization_construction_time:
            vals['modernization_construction_time'] = template.modernization_construction_time
        if template.modernization_inspection_note:
            vals['modernization_inspection_note'] = template.modernization_inspection_note
        if template.modernization_quality_env:
            vals['modernization_quality_env'] = template.modernization_quality_env
        if template.modernization_reservations:
            vals['modernization_reservations'] = template.modernization_reservations
        # Teknisk beskrivning
        for tf in ('tech_general', 'tech_doors', 'tech_machine_room', 'tech_shaft',
                    'tech_car', 'tech_control_panel', 'tech_signalization', 'tech_options'):
            val = getattr(template, tf, False)
            if val:
                vals[tf] = val
        # Serviceavtal
        if template.content:
            vals['content'] = template.content
        if template.billing_interval:
            vals['billing_interval'] = template.billing_interval
        if template.contract_years:
            vals['contract_years'] = template.contract_years
        # Design
        if template.cover_image:
            vals['cover_image'] = template.cover_image
        if template.accent_color and template.accent_color != '#2F4560':
            vals['accent_color'] = template.accent_color
        if template.footer_text:
            vals['footer_text'] = template.footer_text
        for cf in ('cover_feature_1', 'cover_feature_2', 'cover_feature_3'):
            val = getattr(template, cf, False)
            if val:
                vals[cf] = val
        if template.design_version == 'v6':
            for fname, field in template._fields.items():
                if field.type == 'html' and fname in self._fields:
                    vals[fname] = template[fname]
            for fname in ('cover_image', 'accent_color', 'footer_text',
                          'cover_feature_1', 'cover_feature_2', 'cover_feature_3',
                          'delivery_time_info', 'downtime_info',
                          'modernization_construction_time'):
                vals[fname] = template[fname]
        # Offertrader
        lines = []
        for tl in template.line_ids:
            lines.append((0, 0, {
                'sequence': tl.sequence,
                'line_type': tl.line_type,
                'rate_type': tl.rate_type,
                'product_id': tl.product_id.id if tl.product_id else False,
                'name': tl.name,
                'quantity': tl.quantity,
                'uom_id': tl.uom_id.id if tl.uom_id else False,
                'price_unit': tl.price_unit,
            }))
        if lines:
            vals['line_ids'] = lines
        if vals:
            self.write(vals)

    def action_load_standard_prices(self):
        self.ensure_one()
        pricelist = self.partner_id.elevata_pricelist_id
        if not pricelist:
            pricelist = self.env['elevata.pricelist'].search(
                [('active', '=', True)], limit=1, order='id asc'
            )
        if not pricelist:
            raise UserError(_('Ingen prislista hittades. Sätt en prislista på kunden eller skapa en prislista.'))
        existing = self.price_rule_ids
        created = 0
        seen = set()
        for rate in pricelist.rate_ids.sorted('sequence'):
            if rate.rate_type in seen:
                continue
            seen.add(rate.rate_type)
            already = existing.filtered(
                lambda r: r.rule_type == 'hourly' and r.rate_type == rate.rate_type
            )
            if not already:
                self.env['elevata.contract.price.rule'].create({
                    'offer_id': self.id,
                    'rule_type': 'hourly',
                    'rate_type': rate.rate_type,
                    'price': rate.price,
                })
                created += 1
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_preview(self):
        self.ensure_one()
        report = self.env.ref('elevata_offer.action_report_elevata_offer')
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/%s/%s' % (report.report_name, self.id),
            'target': 'new',
        }

    def action_new_version(self):
        self.ensure_one()
        base = (self.name or '').split('/VER')[0]
        same_offer = self.search(['|', ('name', '=', base), ('name', '=like', base + '/VER%')])
        next_version = max(same_offer.mapped('version') + [self.version]) + 1
        new_version = self.copy({
            'name': '%s/VER%d' % (base, next_version),
            'state': 'draft',
            'version': next_version,
            'parent_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'elevata.offer',
            'view_mode': 'form',
            'res_id': new_version.id,
        }

    def action_view_versions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Versioner'),
            'res_model': 'elevata.offer',
            'view_mode': 'tree,form',
            'domain': [('parent_id', '=', self.id)],
        }

    def _create_downstream_objects(self):
        self.ensure_one()
        if self.offer_type == 'serviceavtal':
            if self.service_contract_id:
                return
            self._create_service_contract()
        elif self.offer_type in ('reparation', 'modernisering', 'nyinstallation'):
            self._create_fsm_order()

    def _save_contract_prices(self):
        if self.offer_type != 'serviceavtal':
            return
        for line in self.line_ids.filtered(lambda l: l.equipment_id and l.price_unit > 0):
            vals = {'elevata_contract_price': line.price_unit}
            if line.contract_type_selection:
                vals['elevata_contract_type'] = line.contract_type_selection
            line.equipment_id.write(vals)

    def _create_service_contract(self):
        pricelist = self.partner_id.elevata_pricelist_id
        if not pricelist:
            pricelist = self.env['elevata.pricelist'].search(
                [('active', '=', True)], limit=1, order='id asc'
            )
        contract = self.env['elevata.service.contract'].create({
            'partner_id': self.partner_id.id,
            'state': 'draft',
            'pricelist_id': pricelist.id if pricelist else False,
            'offer_id': self.id,
            'content': self.content or False,
            'date_start': self.contract_start_date or fields.Date.today(),
            'contract_years': int(self.contract_years) if self.contract_years else 1,
            'billing_interval': self.billing_interval or 'yearly',
            'payment_term_id': self.payment_term_id.id if self.payment_term_id else False,
        })
        for line in self.line_ids.filtered(
            lambda l: l.equipment_id and l.contract_type_selection and l.visits_per_year
        ):
            billing_type = 'postpaid' if line.contract_type_selection == 'SERV-VB' else 'prepaid'
            self.env['elevata.service.contract.line'].create({
                'service_contract_id': contract.id,
                'equipment_id': line.equipment_id.id,
                'visits_per_year': line.visits_per_year,
                'price_unit': line.price_unit,
                'contract_type_selection': line.contract_type_selection,
                'billing_type': billing_type,
            })
        for rule in self.price_rule_ids:
            rule.copy({
                'service_contract_id': contract.id,
                'offer_id': False,
            })
        self.service_contract_id = contract
        return contract

    def _create_fsm_order(self):
        order_type = self._get_fsm_order_type()
        todo = self._get_fsm_todo_text()
        locations = self.line_ids.mapped('equipment_id').filtered(lambda l: l.id)
        if not locations:
            locations = self.env['maintenance.equipment']
            vals = {
                'equipment_id': False,
                'customer_id': self.partner_id.id,
                'todo': todo,
            }
            if order_type:
                vals['type'] = order_type.id
            order = self.env['fieldservice.order'].create(vals)
            self.fsm_order_ids = [(4, order.id)]
            return order
        for location in locations:
            vals = {
                'equipment_id': location.id,
                'customer_id': self.partner_id.id,
                'todo': todo,
            }
            if order_type:
                vals['type'] = order_type.id
            order = self.env['fieldservice.order'].create(vals)
            self.fsm_order_ids = [(4, order.id)]
        return True

    def _get_fsm_todo_text(self):
        """Hämta todo-text för FSM-order beroende på offerttyp."""
        if self.offer_type == 'reparation':
            return self.scope_of_work or self.background or self.name
        return self.content or self.name

    def _get_fsm_order_type(self):
        type_map = {
            'reparation': 'Reparation',
            'modernisering': 'Modernisering',
            'nyinstallation': 'Nyinstallation',
        }
        type_name = type_map.get(self.offer_type)
        if type_name:
            return self.env['fieldservice.order.type'].search([('name', 'ilike', type_name)], limit=1)
        return False

    # ── Milstolpe-fakturering ────────────────────────────────────
    MILESTONE_DEFS = {
        '30net': [('Faktura 100%', 100.0)],
        '15net': [('Faktura 100%', 100.0)],
        'immediate': [('Faktura 100%', 100.0)],
        'thirds': [
            ('Vid beställning (1/3)', 33.33),
            ('Vid materialleverans (1/3)', 33.33),
            ('Vid godkänd besiktning (1/3)', 33.34),
        ],
        '5050': [
            ('Vid order (50%)', 50.0),
            ('Vid färdigställt arbete (50%)', 50.0),
        ],
    }

    def _generate_milestones(self):
        """Skapa milstolpe-poster baserat på betalningsstruktur."""
        self.ensure_one()
        if self.milestone_ids:
            return
        structure = self.repair_payment_structure or '30net'
        defs = self.MILESTONE_DEFS.get(structure, [('Faktura 100%', 100.0)])
        for seq, (name, pct) in enumerate(defs, start=1):
            self.env['elevata.offer.milestone'].create({
                'offer_id': self.id,
                'sequence': seq * 10,
                'name': name,
                'percentage': pct,
            })

    def _create_milestone_invoice(self, milestone):
        """Skapa kundfaktura för en milstolpe."""
        milestone.ensure_one()
        offer = milestone.offer_id
        payment_term = self.env.ref(
            'account.account_payment_term_30days', raise_if_not_found=False)
        if offer.repair_payment_structure == '15net':
            payment_term = self.env.ref(
                'account.account_payment_term_15days', raise_if_not_found=False)
        elif offer.repair_payment_structure == 'immediate':
            payment_term = self.env.ref(
                'account.account_payment_term_immediate', raise_if_not_found=False)

        invoice_lines = []
        for line in offer.line_ids:
            invoice_lines.append((0, 0, {
                'name': '%s — %s' % (line.name or line.line_type, milestone.name),
                'quantity': line.quantity * (milestone.percentage / 100.0),
                'price_unit': line.price_unit,
                'tax_ids': [(6, 0, line.tax_ids.ids)] if hasattr(line, 'tax_ids') and line.tax_ids else [],
            }))
        if not invoice_lines:
            invoice_lines.append((0, 0, {
                'name': '%s — %s' % (offer.name, milestone.name),
                'quantity': 1,
                'price_unit': offer.amount_untaxed * (milestone.percentage / 100.0),
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': offer.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_payment_term_id': payment_term.id if payment_term else False,
            'invoice_origin': offer.name,
            'narration': milestone.name,
            'invoice_line_ids': invoice_lines,
        })
        milestone.write({
            'invoice_id': invoice.id,
            'state': 'invoiced',
        })
        return invoice

    def action_invoice_next_milestone(self):
        """Fakturera nästa väntande milstolpe."""
        self.ensure_one()
        pending = self.milestone_ids.filtered(lambda m: m.state == 'pending')
        if not pending:
            raise UserError(_('Alla milstolpar är redan fakturerade.'))
        next_ms = pending.sorted('sequence')[0]
        invoice = self._create_milestone_invoice(next_ms)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Faktura'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
        }

    def action_view_milestones(self):
        self.ensure_one()
        invoices = self.milestone_ids.mapped('invoice_id').filtered(lambda i: i.id)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fakturor'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoices.ids)],
        }

    def action_view_service_contract(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'elevata.service.contract',
            'view_mode': 'form',
            'res_id': self.service_contract_id.id,
        }

    def action_view_fsm_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fieldservice.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.fsm_order_ids.ids)],
        }

    def _auto_save_version(self):
        self.ensure_one()
        self.copy({
            'name': self.name,
            'state': 'sent',
            'parent_id': self.id,
            'version': self.version,
            'service_contract_id': False,
            'fsm_order_ids': [(5, 0, 0)],
        })
        self.write({'version': self.version + 1})
