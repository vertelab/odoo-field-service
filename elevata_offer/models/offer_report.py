import base64
import re
from odoo import api, fields, models
from odoo.tools import html2plaintext
from odoo.tools.image import image_data_uri
from odoo.tools.mail import is_html_empty

TYPE_TITLES = {
    'serviceavtal': 'Serviceavtal',
    'reparation': 'Reparation av hiss',
    'modernisering': 'Modernisering av hiss',
    'nyinstallation': 'Nyinstallation av hiss',
}

COVER_FEATURES = {
    'modernisering': [
        ('shield', 'Ökad säkerhet', 'En tryggare hiss för alla användare'),
        ('wrench', 'Bättre driftsäkerhet', 'Minskad risk för oplanerade stopp'),
        ('clock', 'Längre livslängd', 'En modern och hållbar lösning'),
    ],
    'nyinstallation': [
        ('shield', 'Säker och certifierad', 'Installation enligt gällande standard'),
        ('calendar', 'Tydlig planering', 'Från beställning till slutbesiktning'),
        ('award', 'Garanti och service', 'Trygghet långt efter installation'),
    ],
    'serviceavtal': [
        ('shield', 'Trygg drift', 'Planerat underhåll enligt avtal'),
        ('clock', 'Snabb hjälp', 'Prioriterad jour vid driftstopp'),
        ('file', 'Full kontroll', 'Dokumentation av varje besök'),
    ],
    'reparation': [
        ('shield', 'Ökad säkerhet', 'Åtgärder enligt gällande standard'),
        ('wrench', 'Trygg och säker drift', 'Minskad risk för driftstopp'),
        ('calendar', 'Planerad åtgärd', 'Utförs med minimal påverkan på driften'),
    ],
}

SUMMARY_BENEFITS = {
    'modernisering': [
        ('cpu', 'Modern teknik', 'Uppfyller dagens krav och standarder'),
        ('trend', 'Lägre driftskostnader', 'Effektivare drift och mindre stillestånd'),
        ('leaf', 'Bättre användarupplevelse', 'Tystare, jämnare och säkrare åkning'),
        ('users', 'Minimal påverkan', 'Effektiv installation med tydlig tidsplan'),
    ],
    'nyinstallation': [
        ('cpu', 'Modern teknik', 'Beprövad utrustning av hög kvalitet'),
        ('shield', 'Säkerhet först', 'Uppfyller gällande krav och standarder'),
        ('users', 'Tillgänglighet', 'En hiss som fungerar för alla användare'),
        ('clock', 'Tydlig tidsplan', 'Från planering till slutbesiktning'),
    ],
}

TECH_SECTIONS = [
    ('tech_general', 'Allmänt'),
    ('tech_doors', 'Automatdörrar schakt'),
    ('tech_machine_room', 'Maskinrum'),
    ('tech_shaft', 'Schakt'),
    ('tech_car', 'Hisskorg'),
    ('tech_control_panel', 'Apparatställ'),
    ('tech_signalization', 'Signalisering / tablåer'),
    ('tech_options', 'Optioner'),
]

HERO_IMAGES = {
    'modernisering': 'cabin.jpg',
    'nyinstallation': 'hero_installation.jpg',
    'serviceavtal': 'hero_service.jpg',
    'reparation': 'drive.jpg',
    'enkel': 'doors_repair.jpg',
}

CARD_IMAGES_NEW = ('drive.jpg', 'control_new.jpg', 'cabin.jpg', 'doors_new.jpg')
CARD_IMAGES_REPAIR = ('drive.jpg', 'control_repair.jpg', 'cabin.jpg', 'doors_repair.jpg')

CARD_TITLES = ('Drivsystem', 'Styrning och kontroll', 'Korg och inredning', 'D\u00f6rrar och s\u00e4kerhet')
CARD_FIELDS = ('tech_machine_room', 'tech_control_panel', 'tech_car', 'tech_doors')
CARD_DEFAULTS = (
    'Drivsystem enligt fastst\u00e4lld teknisk specifikation.',
    'Styrning och kontroll enligt fastst\u00e4lld l\u00f6sning.',
    'Korg och inredning enligt fastst\u00e4llda material.',
    'D\u00f6rrar och s\u00e4kerhet enligt objektets f\u00f6ruts\u00e4ttningar.',
)
SERVICE_CARDS = (
    ('Drivsystem', 'Kontroll av maskin, broms och drivning.'),
    ('Styrning och s\u00e4kerhet', 'Kontroll av styrsystem och s\u00e4kerhetskretsar.'),
    ('Korg och inredning', 'Funktionskontroll av korg, belysning och n\u00f6dsignal.'),
    ('D\u00f6rrar', 'Kontroll av d\u00f6rrsystem och d\u00f6rrmotor.'),
)

GOALS = (
    'Fastst\u00e4llda tekniska val',
    'Dokumenterad omfattning',
    'Samordnad tidsplan',
    'Tydliga gr\u00e4nssnitt',
    'Avtalad kontroll',
    'Planerat \u00f6verl\u00e4mnande',
)

NEXT_STEPS = (
    ('check', 'Godk\u00e4nn offerten', 'Returnera offerten med underskrift eller bekr\u00e4fta skriftligt.'),
    ('calendar', 'Vi planerar', 'Vi bekr\u00e4ftar tidsplan och f\u00f6ruts\u00e4ttningar tillsammans med er.'),
    ('tools', 'Genomf\u00f6rande', 'Arbetet utf\u00f6rs enligt \u00f6verenskommen omfattning och dokumenteras.'),
)

TERMS_SECTIONS = [
    ('warranty_terms', 'Garantivillkor'),
    ('payment_terms_text', 'Betalningsvillkor'),
    ('delivery_time', 'Leveranstid'),
    ('delivery_terms', 'Leveransvillkor'),
    ('terms_conditions', 'Allmänna villkor'),
    ('not_included', 'Ingår ej'),
    ('modernization_inspection_note', 'Besiktning'),
    ('modernization_quality_env', 'Kvalitet och miljö'),
    ('modernization_reservations', 'Förtydliganden och reservationer'),
]


class ElevataOfferReport(models.Model):
    _inherit = 'elevata.offer'

    offer_title = fields.Char(
        string='Offertrubrik',
        help='Rubrik på offertens försättsblad, t.ex. "Byte av hisslinor". '
             'Lämna tomt för standardrubrik utifrån offerttypen.',
    )
    simple_layout = fields.Boolean(
        string='Enkel offert (1 sida)',
        help='Skriver ut reparationsofferten på en enda sida. Lämpligt för '
             'mindre arbeten.',
    )

    # ── Designinställningar ────────────────────────────────────────
    cover_image = fields.Binary(
        string='Omslagsbild',
        help='Egen bild på offertens omslag. Lämna tomt för standardbild.',
    )
    cover_image_filename = fields.Char(string='Filnamn omslagsbild')
    accent_color = fields.Char(
        string='Accentfärg',
        default='#2F4560',
        help='Huvudfärg för rubriker, band och tabellhuvuden i PDF:en (hex).',
    )
    footer_text = fields.Text(
        string='Egen sidfotstext',
        help='Ersätter standardsidfoten i PDF:en. Lämna tomt för företagets uppgifter.',
    )
    cover_feature_1 = fields.Char(string='Omslagspunkt 1',
        help='Egen rubrik + text, t.ex. "Trygg drift|Planerat underhåll". '
             'Lämna tomt för standard.')
    cover_feature_2 = fields.Char(string='Omslagspunkt 2')
    cover_feature_3 = fields.Char(string='Omslagspunkt 3')

    design_version = fields.Selection([
        ('legacy', 'Tidigare layout'), ('v6', 'V6')
    ], string='Layoutversion', default='legacy', required=True)
    closing_title = fields.Char(string='Avslutningsrubrik', default='Tack för ert förtroende')
    closing_text = fields.Html(
        string='Avslutningstext', sanitize=True,
        default='<p>Vi ser fram emot ett gott samarbete kring er hiss.</p>'
                '<p>Har ni frågor eller vill diskutera omfattningen är ni varmt välkomna att kontakta oss.</p>',
    )

    def get_report_pdf_preview(self):
        self.ensure_one()
        self.check_access_rights('read')
        self.check_access_rule('read')
        pdf, _ = self.env['ir.actions.report']._render_qweb_pdf(
            'elevata_offer.action_report_elevata_offer', res_ids=self.ids,
        )
        return {
            'data': base64.b64encode(pdf).decode('ascii'),
            'filename': '%s.pdf' % (self.name or 'Offert').replace('/', '-'),
        }

    # ── Rapportval ─────────────────────────────────────────────────

    def get_report_layout(self):
        self.ensure_one()
        if self.offer_type == 'reparation':
            return 'enkel' if self.simple_layout else 'reparation'
        return 'premium'

    # ── Formatering ────────────────────────────────────────────────

    def pdf_money(self, amount, unit=True):
        amount = amount or 0.0
        if abs(amount - round(amount)) < 0.005:
            text = '{:,.0f}'.format(amount)
        else:
            text = '{:,.2f}'.format(amount)
        text = text.replace(',', '\u00a0').replace('.', ',')
        return text + ('\u00a0kr' if unit else '')

    def pdf_qty(self, qty):
        qty = qty or 0.0
        if abs(qty - round(qty)) < 0.005:
            return '%d' % round(qty)
        return ('%.2f' % qty).replace('.', ',')

    def pdf_html(self, fname):
        """Returnerar fältets HTML om det har synligt innehåll, annars False."""
        self.ensure_one()
        value = self[fname]
        return value if value and not is_html_empty(value) else False

    def pdf_title(self):
        self.ensure_one()
        return self.offer_title or TYPE_TITLES.get(self.offer_type, 'Offert')

    def _pdf_selection_label(self, model, fname, value):
        labels = dict(
            self.env[model]._fields[fname]._description_selection(self.env)
        )
        return labels.get(value, value or '')

    # ── Innehåll ───────────────────────────────────────────────────

    def pdf_cover_features(self):
        self.ensure_one()
        custom = []
        for f in (self.cover_feature_1, self.cover_feature_2, self.cover_feature_3):
            if f and '|' in f:
                parts = f.split('|', 1)
                custom.append({'icon': 'check', 'title': parts[0].strip(), 'text': parts[1].strip()})
        if custom:
            return custom
        return [
            {'icon': i, 'title': t, 'text': x}
            for i, t, x in COVER_FEATURES.get(self.offer_type, [])
        ]

    def pdf_benefits(self):
        self.ensure_one()
        return [
            {'icon': i, 'title': t, 'text': x}
            for i, t, x in SUMMARY_BENEFITS.get(self.offer_type, [])
        ]

    def pdf_tech_rows(self):
        self.ensure_one()
        rows = []
        for fname, label in TECH_SECTIONS:
            html = self.pdf_html(fname)
            if html:
                rows.append({'title': label, 'html': html, 'field': fname})
        return rows

    def pdf_terms_sections(self, exclude=()):
        self.ensure_one()
        rows = []
        for fname, label in TERMS_SECTIONS:
            html = self.pdf_html(fname)
            if html and fname not in exclude:
                rows.append({'title': label, 'html': html, 'field': fname})
        if self.ce_compliance_note:
            rows.append({
                'title': 'CE / myndighetskrav',
                'html': '<p>%s</p>' % self.ce_compliance_note,
                'field': 'ce_compliance_note',
            })
        return rows

    def pdf_price_rows(self):
        """En rad per offertrad (namn och delsumma)."""
        self.ensure_one()
        rows = []
        contract_rows = iter(
            self.pdf_contract_rows() if self.offer_type == 'serviceavtal' else []
        )
        for line in self.line_ids:
            row = next(contract_rows, None) if line.contract_type_selection else None
            if row:
                label = '%s \u2014 %s' % (row['location'], row['contract'])
                if row['visits']:
                    label += ', %s' % row['visits']
            else:
                label = line.name or self._pdf_selection_label(
                    'elevata.offer.line', 'line_type', line.line_type)
            rows.append({
                'label': label,
                'amount': line.price_subtotal,
                'note': row['description'] if row else '',
            })
        return rows

    def pdf_price_groups(self):
        """Summerat per radtyp (Arbete, Material, Resa ...)."""
        self.ensure_one()
        totals = {}
        for line in self.line_ids:
            key = line.line_type or 'ovrigt'
            totals[key] = totals.get(key, 0.0) + line.price_subtotal
        return [
            {
                'label': self._pdf_selection_label(
                    'elevata.offer.line', 'line_type', key),
                'amount': amount,
            }
            for key, amount in totals.items()
        ]

    def pdf_scope_rows(self):
        """Omfattning: Pos / Beskrivning / Antal / Enhet / Pris."""
        self.ensure_one()
        rows = []
        for idx, line in enumerate(self.line_ids, start=1):
            rows.append({
                'pos': idx,
                'label': line.name or self._pdf_selection_label(
                    'elevata.offer.line', 'line_type', line.line_type),
                'location': line.equipment_id.name if line.equipment_id else '',
                'qty': self.pdf_qty(line.quantity),
                'unit': line.uom_id.name if line.uom_id else 'st',
                'price': line.price_unit,
                'amount': line.price_subtotal,
            })
        return rows

    def pdf_contract_rows(self):
        """Serviceavtal: en rad per hiss."""
        self.ensure_one()
        rows = []
        for line in self.line_ids.filtered('contract_type_selection'):
            loc = line.equipment_id
            address = ', '.join(
                p for p in [loc.street if loc else '', loc.city if loc else '']
                if p
            )
            name = loc.name if loc else (line.name or '')
            rows.append({
                'location': name,
                'address': '' if address in name else address,
                'description': line.contract_description or '',
                'contract': self._pdf_selection_label(
                    'elevata.offer.line', 'contract_type_selection',
                    line.contract_type_selection)
                if line.contract_type_selection else (line.name or ''),
                'visits': self._pdf_selection_label(
                    'elevata.offer.line', 'visits_per_year',
                    line.visits_per_year) if line.visits_per_year else '',
                'amount': line.price_subtotal,
            })
        return rows

    def pdf_hourly_rules(self):
        self.ensure_one()
        rows = []
        for rule in self.price_rule_ids.filtered(
            lambda r: r.rule_type == 'hourly' and r.price
        ):
            rows.append({
                'label': self._pdf_selection_label(
                    'elevata.contract.price.rule', 'rate_type', rule.rate_type),
                'amount': rule.price,
            })
        return rows

    def pdf_timeline(self):
        self.ensure_one()
        start = self._pdf_selection_label(
            'elevata.offer', 'estimated_start', self.estimated_start)
        days = ('%d arbetsdag%s' % (self.estimated_days, '' if self.estimated_days == 1 else 'ar')
                if self.estimated_days else '')
        if self.offer_type == 'reparation':
            return [
                {'title': 'Planering', 'text': start},
                {'title': 'Utförande', 'text': days or self.delivery_time_info or ''},
                {'title': 'Driftstart',
                 'text': self.downtime_info or 'Direkt efter slutförd åtgärd'},
            ]
        return [
            {'title': 'Projektplanering', 'text': start},
            {'title': 'Leverans',
             'text': self.delivery_time_info or 'Enligt överenskommelse'},
            {'title': 'Installation',
             'text': self.modernization_construction_time or days
             or 'Enligt överenskommelse'},
            {'title': 'Slutbesiktning', 'text': 'Efter slutförd installation'},
        ]

    def pdf_terms_cards(self):
        self.ensure_one()
        validity = ('Offerten gäller t.o.m. %s' % self.validity_date
                    if self.validity_date else '')
        cards = []
        if self.offer_type == 'serviceavtal':
            years = self._pdf_selection_label(
                'elevata.offer', 'contract_years', self.contract_years)
            cards.append({'icon': 'file', 'title': 'Avtalstid',
                          'text': years and ('Avtalstid %s' % years) or ''})
            cards.append({
                'icon': 'card', 'title': 'Betalningsvillkor',
                'text': self.payment_term_id.name or '30 dagar netto'})
        else:
            warranty = self._pdf_selection_label(
                'elevata.offer', 'warranty_years', self.warranty_years)
            cards.append({
                'icon': 'award', 'title': 'Garanti',
                'text': warranty and ('%s garanti' % warranty) or ''})
            cards.append({
                'icon': 'card', 'title': 'Betalningsvillkor',
                'text': self._pdf_selection_label(
                    'elevata.offer', 'repair_payment_structure',
                    self.repair_payment_structure) or '30 dagar netto'})
        cards.append({'icon': 'calendar', 'title': 'Offertens giltighet',
                      'text': validity})
        cards.append({'icon': 'info', 'title': 'Priser',
                      'text': 'Alla priser anges exklusive moms'})
        return cards

    # ── Bilder och faktarutor (design v4) ──

    def pdf_hero(self):
        self.ensure_one()
        if self.cover_image:
            return image_data_uri(self.cover_image)
        key = 'enkel' if self.get_report_layout() == 'enkel' else self.offer_type
        return HERO_IMAGES.get(key, 'cabin.jpg')

    def pdf_hero_is_data_uri(self):
        self.ensure_one()
        return bool(self.cover_image)

    def pdf_accent_color(self):
        self.ensure_one()
        color = (self.accent_color or '').strip()
        return color if re.fullmatch(r'#[0-9a-fA-F]{6}', color) else '#2F4560'

    def pdf_cards(self):
        """Fyra bildkort: drivsystem, styrning, korg, d\u00f6rrar."""
        self.ensure_one()
        repair_set = self.offer_type in ('serviceavtal', 'reparation')
        images = CARD_IMAGES_REPAIR if repair_set else CARD_IMAGES_NEW
        cards = []
        for idx, image in enumerate(images):
            if self.offer_type == 'serviceavtal':
                title, text = SERVICE_CARDS[idx]
            else:
                title = CARD_TITLES[idx]
                text = CARD_DEFAULTS[idx]
            cards.append({'image': image, 'title': title, 'text': text})
        return cards

    def pdf_goals(self):
        self.ensure_one()
        return list(GOALS)

    def pdf_next_steps(self):
        self.ensure_one()
        return [{'icon': i, 'title': t, 'text': x} for i, t, x in NEXT_STEPS]

    def pdf_facts(self):
        """Fastighet, hiss-ID och teknisk specifikation (endast ifyllda rader)."""
        self.ensure_one()
        locations = self.line_ids.mapped('equipment_id')
        sites = []
        for loc in locations:
            address = ', '.join(p for p in [loc.street, loc.city] if p)
            sites.append(address or loc.name or '')
        lifts = [loc.elevator_number for loc in locations if loc.elevator_number]
        specs = []
        for loc in locations:
            if loc.elevator_type_id:
                label = loc.elevator_type_id.name
                if getattr(loc, 'installation_year', False):
                    label += ' (%s)' % loc.installation_year
                if label not in specs:
                    specs.append(label)
        plain = ' '.join(html2plaintext(self.tech_general or '').split())
        rows = []
        if sites:
            rows.append({'label': 'Fastighet', 'value': ' \u00b7 '.join(dict.fromkeys(sites))})
        if lifts:
            rows.append({'label': 'Hiss-ID', 'value': ', '.join(lifts)})
        if specs or plain:
            rows.append({'label': 'Teknisk specifikation', 'value': ', '.join(specs) or plain[:160]})
        return rows

    def pdf_contact(self):
        self.ensure_one()
        user = self.user_id
        parts = [p for p in [user.name if user else '', user.phone if user else '', user.email if user else ''] if p]
        return parts
