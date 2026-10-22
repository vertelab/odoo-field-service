# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, models


class IrUiMenu(models.Model):
    """Remove the menu that belongs to a model this fork does not have.

    Our field service fork replaced fsm.person with hr.employee, so workers
    are no longer managed per location. The "Location Workers" menu survives
    on databases that once ran the OCA fieldservice module — a leftover
    pointing at a model that no longer exists.

    Looked up by name rather than by xmlid: a <record> on a foreign xmlid
    aborts the install when the menu is absent, which is the case on every
    fresh database. Doing nothing where the menu does not exist is the point.
    """

    _inherit = 'ir.ui.menu'

    @api.model
    def _hide_location_workers_menu(self):
        menu = self.search([('name', '=', 'Location Workers')], limit=1)
        if menu:
            menu.active = False
        return True
