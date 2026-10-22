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

{
    'name': 'Field Service: Portal',
    'version': '18.0.1.0.1',
    # Version ledger: 18.0 = Odoo version. 1 = Major. Non regressionable code.
    # 0 = Minor. 1 = Bug fixes
    'summary': 'Customer portal for assets: fault reports, with or without login.',
    'category': 'Field Service',
    'description': '''
Field Service: Portal
=====================

    The one thing a customer needs to do about an asset they own: report a
    fault. And the thing they need to see: which assets they have and what
    state they are in.

    Routes:

        /my/equipment                       the customer's assets
        /my/equipment/<id>                  state and history
        /my/equipment/<id>/report           fault report, logged in
        /my/equipment/report/<token>        fault report by QR, no login

    Every logged-in route scopes to the partner's commercial entity and
    re-checks the record before rendering: a guessed id gives 404, never
    another customer's asset.

    Fault reports create a fieldservice.order with the asset attached, so
    they land in the technician's queue instead of in an inbox someone
    forgets.

    The QR token
    ------------
    A tenant or a passer-by has no account. The token on the sticker
    identifies the asset and nothing else — it grants fault reporting for
    that one record and cannot be used to read it. Regenerating the token
    invalidates every printed sticker, which is the revocation path.

    What this module does not do
    ----------------------------
    It does not know what an inspection is, what a contract is, or what a
    protocol looks like. Those are industry modules: elevator_portal adds
    the inspection history and the agreement, and its own PDF.

    Features:

        - Asset list and detail for the logged-in customer
        - Fault report form, creates a fieldservice order
        - QR token for fault reports without an account
        - Portal home counter
    ''',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_portal',
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'depends': [
        'fieldservice_vrtl',
        'fieldservice_maintenance',
        'portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/portal_templates.xml',
        'views/portal_menu.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
