# -*- coding: utf-8 -*-
{
    'name': 'Field Service: AI Coworkers',
    'version': '18.0.1.0.0',
    'summary': 'OKF-indexering och AI-coworkers for faltsserviceorder.',
    'description': '''
Field Service: AI Coworkers
===========================

Samma monster som `project_ai`, men for faltsservice.

    - OKF: `fieldservice.order` blir sokbar kunskap (okf_body, okf_summary,
      okf_links, okf_dirty, okf_indexed_at) via `ai.okf.mixin`.
    - Artefakttyp: `fieldservice_order` (okf-mixin D12).
    - Brygga: `ai.coworker` far `fieldservice_order_get` /
      `fieldservice_order_set_status`.

VARFOR egen modul och inte project_ai:
    `fieldservice.order` anvander `_inherits = {'project.task': 'task_id'}`.
    Det ar DELEGATION, inte arv — falt pa `project.task` kopieras inte till
    `fieldservice_order`-tabellen och mixinen nar alltsa inte fram. Matt
    2026-10-21: `project_task` hade okf_body/okf_summary/okf_links/okf_dirty/
    okf_indexed_at, `fieldservice_order` hade inga. Mixinen maste laggas
    explicit.
    ''',
    'category': 'Field Service',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_ai',
    'license': 'AGPL-3',
    'depends': [
        'fieldservice_vrtl',
        'ai_agent_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/okf_artifact_types_fieldservice.xml',
        'views/fieldservice_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
