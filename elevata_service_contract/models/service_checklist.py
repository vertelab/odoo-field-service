from odoo import fields, models


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
