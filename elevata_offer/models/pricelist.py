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
    # Bakåtkompatibilitet
    ('overtid',          'Övertid (äldre)'),
    ('jour',             'Jour (äldre)'),
]


class ElevataPricelist(models.Model):
    _name = 'elevata.pricelist'
    _description = 'Elevata Prislista'
    _order = 'name'

    name = fields.Char(string='Prislistans namn', required=True)
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Valuta',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    note = fields.Text(string='Notering')
    rule_ids = fields.One2many(
        'elevata.price.rule',
        'pricelist_id',
        string='Avtalspriser',
    )
    rate_ids = fields.One2many(
        'elevata.price.rate',
        'pricelist_id',
        string='Timpriser',
    )
    markup_ids = fields.One2many(
        'elevata.price.markup',
        'pricelist_id',
        string='Materialpåslag',
    )

    admin_fee_percent = fields.Float(
        string='Administrationsavgift (%)',
        digits=(5, 2),
        default=5.0,
        help='Administrationsavgift i procent som läggs på materialkostnad',
    )

    subscription_price = fields.Float(
        string='Nödtelefon (kr/år)',
        digits=(16, 2),
        default=1800.0,
        help='Standardpris per år för SIM-abonnemang nödtelefon',
    )

    inspection_price = fields.Float(
        string='Biträdande besiktning (kr)',
        digits=(16, 2),
        default=1450.0,
        help='Standardpris för biträdande besiktning',
    )

    def get_price(self, contract_type, visits_per_year):
        self.ensure_one()
        rule = self.rule_ids.filtered(
            lambda r: r.contract_type == contract_type and r.visits_per_year == str(visits_per_year)
        )
        return rule[0].price if rule else 0.0

    def get_rate(self, rate_type, contract_type=None):
        self.ensure_one()
        rate = self.rate_ids.filtered(lambda r: r.rate_type == rate_type)
        return rate[0].price if rate else 0.0

    def get_subscription_price(self):
        self.ensure_one()
        return self.subscription_price or 0.0

    def get_inspection_price(self):
        self.ensure_one()
        return self.inspection_price or 0.0

    def get_markup(self, cost):
        self.ensure_one()
        if not self.markup_ids or cost <= 0:
            return 1.0
        for row in self.markup_ids.sorted('from_amount'):
            if cost >= row.from_amount and (row.to_amount == 0 or cost <= row.to_amount):
                return row.multiplier
        return 1.0


class ElevataPriceRule(models.Model):
    _name = 'elevata.price.rule'
    _description = 'Elevata Prisregel'
    _order = 'contract_type, visits_per_year'

    pricelist_id = fields.Many2one(
        'elevata.pricelist',
        string='Prislista',
        required=True,
        ondelete='cascade',
    )
    contract_type = fields.Selection(
        CONTRACT_TYPE,
        string='Avtalstyp',
        required=True,
    )
    visits_per_year = fields.Selection(
        VISITS_PER_YEAR,
        string='Besök/år',
        required=True,
    )
    price = fields.Float(
        string='Årsavgift (kr/år)',
        digits=(16, 2),
    )
    note = fields.Char(string='Notering')


class ElevataPriceRate(models.Model):
    _name = 'elevata.price.rate'
    _description = 'Elevata Timprisregel'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Ordning', default=10)
    pricelist_id = fields.Many2one(
        'elevata.pricelist',
        string='Prislista',
        required=True,
        ondelete='cascade',
    )
    rate_type = fields.Selection(
        RATE_TYPE,
        string='Tidtyp',
        required=True,
    )
    price = fields.Float(
        string='Timpris (kr/h)',
        digits=(16, 2),
    )
    note = fields.Char(string='Notering')


class ElevataPriceMarkup(models.Model):
    _name = 'elevata.price.markup'
    _description = 'Elevata Materialpåslag'
    _order = 'from_amount'

    pricelist_id = fields.Many2one(
        'elevata.pricelist',
        string='Prislista',
        required=True,
        ondelete='cascade',
    )
    from_amount = fields.Float(
        string='Fr.o.m. (kr)',
        digits=(16, 2),
        required=True,
        default=0.0,
    )
    to_amount = fields.Float(
        string='T.o.m. (kr)',
        digits=(16, 2),
        help='Lämna 0 för obegränsat (sista tröskel)',
    )
    multiplier = fields.Float(
        string='Multiplikator',
        digits=(16, 2),
        required=True,
        default=1.0,
    )
    note = fields.Char(string='Notering')


class ResPartnerPricelistExt(models.Model):
    _inherit = 'res.partner'

    elevata_pricelist_id = fields.Many2one(
        'elevata.pricelist',
        string='Elevata Prislista',
        help='Prislista som automatiskt används på nya offerter för denna kund',
    )
