# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo SA, Open Source Management Solution, third party addon
#    Copyright (C) 2025- Vertel Sverige AB (<https://vertel.se>).
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
    'name': 'Fieldservice: AI Coworkers',
    'version': '18.0.2.0.0',
    'summary': 'AI coworker for field service — dispatcher + specialist agents.',
    'category': 'Fieldservice',
    'description': '''
Fieldservice: AI Coworkers
==========================

AI coworker for field service orders (fieldservice.order).

Agents:

    - Servicedispatcher (supervisor) — triage, planering, delegering
    - Severity Analyst — allvarlighetsgrad Low/Medium/Critical
    - Time Estimator — tidsuppskattning 1-4 timmar
    - Work Planner — planerat start/slut + tillgänglig tekniker
    - Service Assistant — chatt som svarar teknikern om ordern

Ported from the legacy ai.agent/ai.quest generation (18.0.1.0.4) to the
ai.coworker architecture, matching project_ai.
    ''',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_vrtl_ai',
    'images': ['static/description/banner.png'],  # 560x280 px.
    'license': 'AGPL-3',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'depends': [
        'ai_agent_core',
        'fieldservice_vrtl',
        'fieldservice_hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/fieldservice_tools.xml',
        'data/fieldservice_skills.xml',
        'data/fieldservice_agents.xml',
        'data/fieldservice_coworkers.xml',
    ],
    # 2026-10-22: SUPERSEDED av fieldservice_ai.
    # Agenterna, skillsen, verktygen och coworkern flyttades dit — den
    # modulen ager redan fieldservice.order-AI:n (bryggmetoder + OKF-mixin)
    # och ar installerad. Tva moduler med samma syfte ar en falla for
    # nasta person; en modul gor allt.
    'installable': False,
    'auto_install': False,
    'application': False,
}
