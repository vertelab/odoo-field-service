from odoo import models, fields, api


CONTRACT_TYPE = [
    ('SERV-VB', 'Vid Behov'),
    ('SERV-STD', 'Standard'),
    ('SERV-FULL', 'Fullservice'),
    ('SERV-GAR', 'Garanti'),
]

VISITS_PER_YEAR = [
    ('1', '1 besök/år'),
    ('2', '2 besök/år'),
    ('4', '4 besök/år'),
    ('6', '6 besök/år'),
]

LINE_TYPE = [
    ('arbete', 'Arbete'),
    ('material', 'Material'),
    ('resa', 'Resa'),
    ('nodtelefon', 'Nödtelefon'),
    ('besiktning', 'Biträdande besiktning'),
    ('ovrigt', 'Övrigt'),
]

RATE_TYPE = [
    ('normaltid',        'Normaltid (mån-fre 07:00-16:00)'),
    ('overtid_1_2h',     'Övertid 1-2 h'),
    ('overtid_2h_plus',  'Övertid efter 2 h'),
    ('lordag',           'Lördag'),
    ('sondag_helgdag',   'Söndag/Helgdag'),
    ('storhelg',         'Storhelg'),
    ('beredskap_vardag', 'Beredskap vardag'),
    ('beredskap_helg',   'Beredskap helg'),
    ('jourutryckning',   'Jourutryckning (min 3 h)'),
    ('restid',           'Restid'),
    ('servicebil_mil',   'Servicebil (kr/mil)'),
    ('servicebil_tid',   'Servicebil tid'),
    ('servicebil_fast',  'Servicebil fast avgift (kr)'),
    ('verktygsavgift',   'Verktygsavgift'),
]


class ElevataOfferLine(models.Model):
    _name = 'elevata.offer.line'
    _description = 'Elevata Offertrad'
    _order = 'sequence, id'

    offer_id = fields.Many2one(
        'elevata.offer',
        string='Offert',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Hiss',
        domain="[('elevator_type_id', '!=', False)]",
    )
    contract_type_selection = fields.Selection(
        CONTRACT_TYPE,
        string='Avtalstyp',
    )
    visits_per_year = fields.Selection(
        VISITS_PER_YEAR,
        string='Besök/år',
    )
    contract_description = fields.Text(
        string='Vad ingår',
        compute='_compute_contract_description',
        store=True,
    )
    line_type = fields.Selection(
        LINE_TYPE,
        string='Typ',
        required=True,
        default='arbete',
    )
    rate_type = fields.Selection(
        RATE_TYPE,
        string='Tidtyp',
        help='Tidtyp för timdebitering (normaltid/övertid/jour)',
    )
    name = fields.Char(string='Beskrivning')
    product_id = fields.Many2one(
        'product.product',
        string='Produkt',
    )
    quantity = fields.Float(string='Antal', default=1.0)
    uom_id = fields.Many2one(
        'uom.uom',
        string='Enhet',
    )
    price_unit = fields.Float(string='À-pris', digits=(16, 2))
    list_price = fields.Float(
        string='Standardpris',
        digits=(16, 2),
        help='Standardpris från prislistan (fylls i automatiskt)',
    )
    discount = fields.Float(
        string='Rabatt %',
        digits=(5, 2),
        help='Rabatt i procent mot standardpriset',
    )
    saving = fields.Float(
        string='Besparing',
        compute='_compute_saving',
        store=True,
        digits=(16, 2),
    )
    price_subtotal = fields.Float(
        string='Delsumma',
        compute='_compute_price_subtotal',
        store=True,
    )

    include_subscription = fields.Boolean(
        string='Inkl. Nödtelefon',
        default=False,
    )
    subscription_provider = fields.Char(string='Operatör')
    subscription_sale_price = fields.Float(
        string='Ab.pris (kr/mån)',
        digits=(16, 2),
    )
    subscription_binding_months = fields.Integer(
        string='Bindningstid (mån)',
        default=12,
    )

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit

    @api.depends('list_price', 'price_unit', 'quantity')
    def _compute_saving(self):
        for line in self:
            if line.list_price > 0 and line.list_price > line.price_unit:
                line.saving = (line.list_price - line.price_unit) * (line.quantity or 1)
            else:
                line.saving = 0.0

    @api.depends('contract_type_selection')
    def _compute_contract_description(self):
        descriptions = {
            'SERV-VB': 'Behovsbaserat avtal utan fast kostnad. Fakturering per besök. Jour och reservdelar enligt prislista.',
            'SERV-STD': 'Fast årsavgift. Planerade besök per år. Jour och reservdelar enligt prislista. Automatisk serviceplanering.',
            'SERV-FULL': 'Fast årsavgift. Planerade besök per år. Jour och utvalda reservdelar ingår. Prioriterad service dygnet runt.',
            'SERV-GAR': 'Garantiavtal utan servicekostnad. Planerade besök enligt garantivillkor. Jour och reservdelar ingår per garantivillkor.',
        }
        for line in self:
            line.contract_description = descriptions.get(line.contract_type_selection, False)

    @api.onchange('contract_type_selection', 'visits_per_year', 'rate_type', 'line_type')
    def _onchange_auto_name(self):
        if self.offer_id.offer_type != 'serviceavtal':
            return
        contract_labels = dict(CONTRACT_TYPE)
        visits_labels = dict(VISITS_PER_YEAR)
        rate_labels = dict(RATE_TYPE)
        if self.line_type == 'arbete' and self.rate_type:
            parts = [rate_labels.get(self.rate_type, '')]
            if self.contract_type_selection:
                parts.append(contract_labels.get(self.contract_type_selection, ''))
            self.name = ' — '.join(p for p in parts if p)
        elif self.contract_type_selection:
            parts = [contract_labels.get(self.contract_type_selection, '')]
            if self.visits_per_year:
                parts.append(visits_labels.get(self.visits_per_year, ''))
            self.name = ' — '.join(p for p in parts if p)

    @api.onchange('discount')
    def _onchange_discount(self):
        if self.list_price > 0 and self.discount >= 0:
            self.price_unit = self.list_price * (1.0 - self.discount / 100.0)

    def _get_active_pricelist(self):
        if self.offer_id and self.offer_id.partner_id:
            pl = self.offer_id.partner_id.elevata_pricelist_id
            if pl:
                return pl
        return self.env['elevata.pricelist'].search(
            [('active', '=', True)], limit=1, order='id asc'
        )

    def _get_contract_rule(self, rule_type, rate_type=None):
        def _match(rule_set):
            rules = rule_set.filtered(
                lambda r: r.rule_type == rule_type
                and (not r.equipment_id or r.equipment_id == self.equipment_id)
                and (not r.rate_type or r.rate_type == rate_type)
                and (not r.contract_type or r.contract_type == self.contract_type_selection)
            )
            if not rules:
                return False
            return rules.sorted(
                key=lambda r: (bool(r.equipment_id), bool(r.rate_type), bool(r.contract_type)),
                reverse=True
            )[0]

        contract = self.offer_id.service_contract_id
        if contract and contract.price_rule_ids:
            result = _match(contract.price_rule_ids)
            if result:
                return result

        offer = self.offer_id
        if offer and offer.price_rule_ids:
            return _match(offer.price_rule_ids)

        return False

    def _apply_list_price(self, list_price, unit_price):
        """Sätter standardpriset. À-priset följer med så länge det inte ändrats manuellt."""
        old_list = self.list_price
        old_unit = self.price_unit
        follows_list = abs(old_unit - old_list * (1.0 - (self.discount or 0.0) / 100.0)) < 0.005
        self.list_price = list_price
        if not old_unit or follows_list:
            if self.discount and unit_price == list_price:
                unit_price = list_price * (1.0 - self.discount / 100.0)
            self.price_unit = unit_price

    @api.onchange('equipment_id', 'contract_type_selection', 'visits_per_year', 'rate_type', 'line_type')
    def _onchange_lookup_price(self):
        # Reparation/övriga offerttyper: hämta timpris utan contract_type
        if not self.contract_type_selection and self.offer_id.offer_type != 'serviceavtal':
            if self.line_type == 'arbete' and self.rate_type:
                pricelist = self._get_active_pricelist()
                if pricelist:
                    price = pricelist.get_rate(self.rate_type)
                    if price:
                        self._apply_list_price(price, price)
            return

        if not self.contract_type_selection:
            return

        # Arbete/timdebitering: look up hourly rate
        if self.line_type == 'arbete' and self.rate_type:
            # Tier 0: contract-specific hourly rule
            rule = self._get_contract_rule('hourly', rate_type=self.rate_type)
            if rule:
                if rule.is_included:
                    self.list_price = 0.0
                    self.price_unit = 0.0
                    return
                if rule.price > 0:
                    self._apply_list_price(rule.price, rule.price)
                    return
                if rule.discount_pct > 0:
                    pricelist = self._get_active_pricelist()
                    if pricelist:
                        base = pricelist.get_rate(self.rate_type)
                        if base:
                            self._apply_list_price(base, round(base * (1.0 - rule.discount_pct / 100.0), 2))
                            return
            # Tier 1: pricelist rate
            pricelist = self._get_active_pricelist()
            if pricelist:
                price = pricelist.get_rate(self.rate_type)
                if price:
                    self._apply_list_price(price, price)
            return

        # Annual fee: need both contract_type and visits_per_year
        if not self.visits_per_year:
            return

        # Tier 1: location's last agreed price (if contract type matches)
        # SERV-VB hoppas alltid över — prislistan styr (0 kr)
        if self.contract_type_selection != 'SERV-VB':
            if self.equipment_id and self.equipment_id.elevata_contract_price > 0:
                if self.equipment_id.elevata_contract_type == self.contract_type_selection:
                    price = self.equipment_id.elevata_contract_price
                    self._apply_list_price(price, price)
                    return

        # Tier 1.5: contract-specific annual fee rule
        rule = self._get_contract_rule('annual_fee')
        if rule:
            if rule.price > 0:
                self._apply_list_price(rule.price, rule.price)
                return
            if rule.discount_pct > 0:
                pricelist = self._get_active_pricelist()
                if pricelist:
                    base = pricelist.get_price(self.contract_type_selection, self.visits_per_year)
                    if base:
                        self._apply_list_price(base, round(base * (1.0 - rule.discount_pct / 100.0), 2))
                        return

        # Tier 2: partner's pricelist
        pricelist = self._get_active_pricelist()
        if pricelist:
            price = pricelist.get_price(self.contract_type_selection, self.visits_per_year)
            if price:
                self._apply_list_price(price, price)

    @api.onchange('list_price')
    def _onchange_list_price(self):
        if self.list_price > 0 and self.discount:
            self.price_unit = self.list_price * (1.0 - self.discount / 100.0)
        elif self.list_price > 0 and not self.price_unit:
            self.price_unit = self.list_price

    @api.onchange('include_subscription')
    def _onchange_include_subscription(self):
        if not self.include_subscription:
            return
        if self.subscription_sale_price:
            return
        pricelist = self._get_active_pricelist()
        if pricelist:
            price = pricelist.get_subscription_price()
            if price:
                self.subscription_sale_price = price

    @api.onchange('line_type')
    def _onchange_line_type(self):
        defaults = {
            'nodtelefon': 'SIM-abonnemang nödtelefon',
            'besiktning': 'Biträdande besiktning',
        }
        if self.line_type in defaults and not self.name:
            self.name = defaults[self.line_type]
        if self.line_type == 'nodtelefon' and not self.price_unit:
            pricelist = self._get_active_pricelist()
            if pricelist:
                price = pricelist.get_subscription_price()
                if price:
                    self.list_price = price
                    self.price_unit = price
        if self.line_type == 'besiktning' and not self.price_unit:
            pricelist = self._get_active_pricelist()
            if pricelist:
                price = pricelist.get_inspection_price()
                if price:
                    self.list_price = price
                    self.price_unit = price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.lst_price
            self.uom_id = self.product_id.uom_id
