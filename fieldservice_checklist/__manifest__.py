{
    'name': "Field Service: Checklist",
    'version': '18.0.1.1.0',
    'depends': ['fieldservice_vrtl', 'maintenance'],
    'author': "Vertel Sverige AB",
    'website': "https://github.com/vertelab/odoo-field-service",
    'category': 'Field Service',
    'license': 'AGPL-3',
    'images': ['static/description/banner.png'],
    'description': """
Field Service: Checklist
========================

Checklists on a field service work order.

Three models, three jobs:

* ``fieldservice.checklist`` — a reusable template
* ``fieldservice.checklist.line`` — one item in that template
* ``fieldservice.checklist.item`` — a filled-in item on a work order

The split between template and item is the whole point. A template is
edited; an item is history. The text is copied at creation, so an
inspection done in March still reads the same in December even after
someone rewrites the template.

Shaped after ``quality.point`` / ``quality.check`` on purpose — a later
move to OCA quality becomes a mapping rather than a rewrite.

WHERE THIS BELONGS
------------------
The checklist belongs to the work order, not to the asset. A technician
is dispatched to an order; the order carries the list of what to check.

The asset-level checklist is a different thing — a standing inspection
plan on ``maintenance.equipment`` — and lives elsewhere. This module
does not touch it.

WHAT THIS MODULE DOES NOT DO
----------------------------
It ships no templates. Templates are data, and data belongs to whoever
owns the domain. A customer module adds its own templates and they are
picked up here.
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/fieldservice_checklist_views.xml',
        'views/fieldservice_order_views.xml',
        'views/menu_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
