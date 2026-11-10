# -*- coding: utf-8 -*-
"""Rename the Vertel field service modules to their _vrtl names.

Every module in this repository now carries the _vrtl suffix, so a module
name can never be confused with an OCA module of the same name. Before this
change three names collided with OCA/field-service (fieldservice_maintenance,
fieldservice_portal, fieldservice_route) and which one won depended on the
order of addons_path.

Odoo keys installed modules on ir_module_module.name. Renaming the directory
alone leaves the old row behind and the new module looks uninstalled — every
upgrade would then be a fresh install on a live database. This script
rewrites the rows in place and moves the external ids, so the modules stay
installed and keep their data.

Runs as pre-migrate on fieldservice_vrtl, the base module that every other
module here depends on.
"""
import logging

_logger = logging.getLogger(__name__)

# Order matters: the adaptation layer (old fieldservice_maintenance_vrtl) is
# renamed BEFORE the base module takes that name, otherwise the two collide.
RENAME = [
    ('fieldservice_maintenance_vrtl', 'fieldservice_maintenance_adapt_vrtl'),
    ('fieldservice_account_analytic', 'fieldservice_account_analytic_vrtl'),
    ('fieldservice_checklist', 'fieldservice_checklist_vrtl'),
    ('fieldservice_history', 'fieldservice_history_vrtl'),
    ('fieldservice_hr', 'fieldservice_hr_vrtl'),
    ('fieldservice_maintenance', 'fieldservice_maintenance_vrtl'),
    ('fieldservice_media', 'fieldservice_media_vrtl'),
    ('fieldservice_mobile', 'fieldservice_mobile_vrtl'),
    ('fieldservice_order_type_color', 'fieldservice_order_type_color_vrtl'),
    ('fieldservice_portal', 'fieldservice_portal_vrtl'),
    ('fieldservice_report', 'fieldservice_report_vrtl'),
    ('fieldservice_route', 'fieldservice_route_vrtl'),
    ('fieldservice_sla', 'fieldservice_sla_vrtl'),
    ('fieldservice_vrtl_account', 'fieldservice_vrtl_account_vrtl'),
    ('fieldservice_vrtl_ai', 'fieldservice_vrtl_ai_vrtl'),
]


def migrate(cr, version):
    if not version:
        return
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    Module = env['ir.module.module'].sudo()
    Data = env['ir.model.data'].sudo()

    for old, new in RENAME:
        if Module.search_count([('name', '=', new)]):
            _logger.info("fieldservice rename: %s finns redan, hoppar", new)
            continue
        mod = Module.search([('name', '=', old)], limit=1)
        if not mod:
            continue
        mod.write({'name': new})
        _logger.info("ir_module_module: %s -> %s", old, new)

    # External ids carry the module name as prefix. A stale prefix means every
    # xmlid in the module resolves to nothing after the rename.
    for old, new in RENAME:
        ids = Data.search([('module', '=', old)])
        if ids:
            ids.write({'module': new})
            _logger.info("ir.model.data: %s.* -> %s.* (%d st)", old, new, len(ids))
