# -*- coding: utf-8 -*-
{
    'name': 'Field Service: AI Coworker',
    'version': '18.0.1.0.0',
    'summary': 'AI coworker for field service — order context, tools and skills.',
    'description': '''
Field Service AI Coworker
=========================

    Built on ai_agent_core, the same pattern as project_ai.

    Features:

        - Session context: `fsm_order_id` and `fsm_location_id` on
          ai.coworker.session, so cost context, lineage and memory attach
          to the work order.
        - Resolver `fieldservice_partner`: derives the customer from the
          order's location (fsm.location inherits res.partner).
        - Tools: order_get, order_set_stage, order_update_fields,
          order_add_message.
        - Coworker "Field Service" (supervisor) with its own skills.

    WHY A SEPARATE MODULE: the existing `fieldservice_vrtl_ai` is built on
    the old `ai_agent` stack — the same incompatibility as the old
    helpdesk_ai. This module is the ai_agent_core-native replacement.

    MODEL CHOICE: OCA `fieldservice` (fsm.order, fsm.location). A field
    service order has no partner_id of its own — the customer is reached
    through `location_id.partner_id`, because fsm.location inherits
    res.partner.
    ''',
    'category': 'Field Service',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se',
    'license': 'AGPL-3',
    'depends': [
        'fieldservice',
        'ai_agent_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/fieldservice_tools.xml',
        'data/fieldservice_skills.xml',
        'data/fieldservice_coworkers.xml',
        'data/fieldservice_agents.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
