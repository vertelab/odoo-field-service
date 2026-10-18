import logging
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)


class ResCalendarSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ics_url_eve = fields.Char(
        string='Enter the URL of the ICS file',
        config_parameter='holiday.url.ics',
        default='https://www.webcal.guru/sv-SE/ladda_ner_kalendern?calendar_instance_id=86')

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if vals_list.get("ics_url_eve"):
            # Scheduling lives in data/cron_tasks.xml (cron.task), not here:
            # a cron created at settings-save time cannot be verified against
            # the code and duplicated on every save. See design D7.
            if not self.env['res.users'].search([('login', '=', "holidays")]):
                self.env['res.users'].sudo().create({'name': "Holidays", 'login': "holidays"})
        return res
