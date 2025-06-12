from odoo import api, fields, models, _
from datetime import date as date_type
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fieldservice_project_id = fields.Many2one(
        'project.project',
        string="Default Field Service Project",
        config_parameter='fieldservice.default_project_id'
    )
