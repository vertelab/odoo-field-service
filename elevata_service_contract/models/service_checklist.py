from odoo import api, fields, models


class ServiceChecklist(models.Model):
    """A reusable checklist template.

    The ``elevata.service.checklist`` family lives here because
    ``elevata_service_contract`` is the module that uses it — the templates
    generate the checklist lines on a work order. The models kept their
    original names so existing references and tables keep resolving.
    """

    _name = 'elevata.service.checklist'
    _description = 'Service Checklist Template'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    elevator_type_ids = fields.Many2many(
        'maintenance.elevator.type',
        'service_checklist_elevator_type_rel',
        'checklist_id',
        'elevator_type_id',
        string='Elevator Types',
        help='Leave empty to apply to all elevator types',
    )
    active = fields.Boolean(string='Active', default=True)
    line_ids = fields.One2many(
        'elevata.service.checklist.line',
        'checklist_id',
        string='Items',
    )
    line_count = fields.Integer(
        string='Items',
        compute='_compute_line_count',
    )

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)


class ServiceChecklistLine(models.Model):
    _name = 'elevata.service.checklist.line'
    _description = 'Service Checklist Template Line'
    _order = 'sequence, id'

    checklist_id = fields.Many2one(
        'elevata.service.checklist',
        string='Checklist',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(string='Check Item', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    note = fields.Text(string='Note / Instruction')


class ServiceChecklistItem(models.Model):
    _name = 'elevata.service.checklist.item'
    _description = 'Service Checklist Item (on Work Order)'
    _order = 'sequence, id'

    fsm_order_id = fields.Many2one(
        'fieldservice.order',
        string='Work Order',
        required=True,
        ondelete='cascade',
    )
    checklist_line_id = fields.Many2one(
        'elevata.service.checklist.line',
        string='Template Item',
        ondelete='set null',
    )
    name = fields.Char(string='Check Item', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    done = fields.Boolean(string='Done', default=False)
    note = fields.Text(string='Note')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') and vals.get('checklist_line_id'):
                line = self.env['elevata.service.checklist.line'].browse(
                    vals['checklist_line_id']
                )
                vals['name'] = line.name
        return super().create(vals_list)


class LocationChecklistLine(models.Model):
    """A checklist line that belongs to one piece of equipment.

    The model was called ``elevata.location.checklist.line`` when the asset
    was ``fsm.location``. The asset is now ``maintenance.equipment``, so the
    owning field is ``equipment_id`` — which is also the column the table
    already has.
    """

    _name = 'elevata.location.checklist.line'
    _description = 'Location-specific Checklist Line'
    _order = 'sequence, id'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Elevator',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(string='Task', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
