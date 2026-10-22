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
    'name': 'Field Service: Report',
    'version': '18.0.1.0.0',
    # Version ledger: 18.0 = Odoo version. 1 = Major. Non regressionable code.
    # 0 = Minor. 1 = Bug fixes
    'summary': 'Service report per work order, signed on site.',
    'category': 'Field Service',
    'description': '''
Field Service: Report
=====================

    The document the technician leaves behind.

    A work order lives in Odoo; the customer needs a piece of paper saying
    what was done, when, by whom, and that they accepted it. That is the
    service report, and it is the same in every trade — a plumber, an alarm
    fitter and an elevator technician hand over the same document.

    Contents:

        the order, the asset, the customer
        the technician and the date
        what was done — the order description
        the checklist, if the order carried one
        a signature line for the customer

    The signature is the point. It is what settles a later disagreement
    about whether the work was done and accepted. Without it the report is
    an internal note printed on customer paper.

    Overriding
    ----------
    The template is a starting point. An industry module inherits it and
    adds what its trade needs — a protocol number, a statutory reference, a
    second signature — without touching this one.

    Features:

        - Service report per work order
        - Checklist included when the order has one
        - Customer signature line
        - Print button on the order form
    ''',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_report',
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'depends': [
        'fieldservice_vrtl',
        'fieldservice_maintenance',
        'fieldservice_order_type_color',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/report_templates.xml',
        'views/report_actions.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
