# Copyright (C) 2026 Vertel Sverige AB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def _elevata_get_or_create_project(self, name):
        """Return the project with this name, creating it if missing.

        Called from data/project_data.xml so the seed data stays idempotent
        on databases where the project already exists.
        """
        project = self.search([('name', '=', name)], limit=1)
        if not project:
            project = self.create({
                'name': name,
                'allow_timesheets': True,
            })
        return project.id
