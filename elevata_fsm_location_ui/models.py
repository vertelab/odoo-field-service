from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _elevata_hide_location_workers(self):
        """Deactivate the Location Workers menu if it exists.

        Our field service fork removed fsm.person, so there is no per-location
        worker list to show. The menu survives on databases that once ran the
        OCA fieldservice module; hide it there and do nothing elsewhere.
        """
        menu = self.search([('name', '=', 'Location Workers')], limit=1)
        if menu:
            menu.active = False
        return True
