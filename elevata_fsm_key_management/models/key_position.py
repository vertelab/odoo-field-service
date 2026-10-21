from odoo import _, api, fields, models


class KeyPosition(models.Model):
    _name = 'elevata.key.position'
    _description = 'Key Position'
    _order = 'name'

    name = fields.Char(string="Name", required=True, default='New', readonly=True)
    street = fields.Char(string="Street")
    zip = fields.Char(string="ZIP")
    city = fields.Char(string="City")
    position_type = fields.Selection([
        ('key_tube', 'Key Tube'),
        ('shaft', 'Shaft'),
        ('safe', 'Safe'),
        ('other', 'Other'),
    ], string="Position Type", required=True)
    code = fields.Char(string="Code")
    key_ids = fields.One2many('elevata.key', 'position_id', string="Keys")
    elevator_ids = fields.Many2many(
        'maintenance.equipment',
        compute='_compute_elevator_ids',
        store=True,
        readonly=True,
    )
    active = fields.Boolean(string="Active", default=True)

    # Geolocation
    latitude = fields.Float(string="Latitude", digits=(16, 8))
    longitude = fields.Float(string="Longitude", digits=(16, 8))
    date_localization = fields.Date(string="Geolocation Date")
    owner_id = fields.Many2one('res.partner', string="Owner")

    GEO_FIELDS = {'street', 'zip', 'city'}

    def _compute_position_name(self):
        parts = ['NP']
        if self.street:
            parts.append(self.street)
        if self.city:
            parts.append(self.city)
        return ':'.join(parts)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.name = rec._compute_position_name()
        to_geo = records.filtered(lambda r: r.street or r.city)
        if to_geo:
            to_geo._geo_localize_all()
        return records

    def write(self, vals):
        res = super().write(vals)
        if self.GEO_FIELDS & set(vals.keys()):
            for rec in self:
                rec.name = rec._compute_position_name()
            to_geo = self.filtered(lambda r: r.street or r.city)
            if to_geo:
                to_geo._geo_localize_all()
        return res

    @api.depends('key_ids', 'key_ids.elevator_ids')
    def _compute_elevator_ids(self):
        for position in self:
            position.elevator_ids = position.key_ids.mapped('elevator_ids')

    @api.model
    def _geo_localize(self, street='', zip_code='', city='', country=''):
        geo_obj = self.env['base.geocoder']
        search = geo_obj.geo_query_address(
            street=street, zip=zip_code, city=city, country=country
        )
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(city=city, country=country)
            result = geo_obj.geo_find(search, force_country=country)
        return result

    def _geo_localize_all(self):
        not_located = self.env['elevata.key.position']
        for position in self.with_context(lang='en_US'):
            if not position.street and not position.city:
                continue
            result = self._geo_localize(
                street=position.street,
                zip_code=position.zip,
                city=position.city,
                country='Sweden',
            )
            if result:
                position.write({
                    'latitude': result[0],
                    'longitude': result[1],
                    'date_localization': fields.Date.context_today(position),
                })
            else:
                not_located |= position

        if not_located:
            self.env['bus.bus']._sendone(
                self.env.user.partner_id, 'simple_notification', {
                    'type': 'danger',
                    'title': _("Warning"),
                    'message': _(
                        "Could not find coordinates for these positions: %s",
                        ', '.join(not_located.mapped('name')),
                    ),
                }
            )
        return True

    def action_geo_localize(self):
        return self._geo_localize_all()
