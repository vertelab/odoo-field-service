from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Key(models.Model):
    _name = 'elevata.key'
    _description = 'Key'
    _order = 'code, name'

    name = fields.Char(string="Name", required=True, default='New', readonly=True)
    position_id = fields.Many2one('elevata.key.position', string="Key Position")
    code = fields.Char(string="Code", copy=False)
    key_type = fields.Selection([
        ('service', 'Service Key'),
        ('master', 'Master Key'),
        ('emergency', 'Emergency Key'),
        ('user', 'User Key'),
        ('other', 'Other'),
    ], string="Key Type", default='service', required=True)
    elevator_ids = fields.Many2many('maintenance.equipment', string="Elevators")
    owner_id = fields.Many2one('res.partner', string="Owner")
    issued_date = fields.Date(string="Issued On")
    returned_date = fields.Date(string="Returned On")
    notes = fields.Text(string="Notes")
    active = fields.Boolean(string="Active", default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('elevata.key') or 'New'
                )
        return super().create(vals_list)

    @api.constrains('code')
    def _check_code_unique(self):
        for key in self:
            if key.code:
                if self.search_count([('code', '=', key.code), ('id', '!=', key.id)]):
                    raise ValidationError(_("Key code must be unique!"))
