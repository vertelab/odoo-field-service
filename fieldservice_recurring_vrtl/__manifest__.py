{
    'name': 'Field Service: Recurring Orders (Vertel)',
    'version': '18.0.1.0.0',
    'category': 'Field Service',
    'summary': 'Recurring field service orders (Vertel fork)',
    'description': """
Field Service: Recurring Orders (Vertel)
========================================

Recurring orders for the Vertel field service fork.

The OCA module ``fieldservice_recurring`` provides a template that
generates field service orders on a schedule (service visits, statutory
inspections, maintenance intervals). It is not available for the Vertel
fork, which replaces ``fieldservice`` with ``fieldservice_vrtl``.

This module provides the minimum needed by dependent modules:

* ``fsm.recurring`` — the recurrence template: interval, unit, next
  date, and the order type to stamp on generated orders.
* ``fieldservice.order.fsm_recurring_id`` — link from an order back to
  the template that produced it.
* ``action_view_fsm_recurring()`` — smart button on the order form.

Generation itself is intentionally left simple: ``_generate_orders()``
creates one order per due period and advances ``next_date``. It is
idempotent — running it twice on the same day does not create duplicate
orders.
    """,
    'author': 'Vertel Sverige AB',
    'maintainer': 'Vertel Sverige AB',
    'license': 'AGPL-3',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_recurring_vrtl',
    'depends': [
        'fieldservice_vrtl',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fsm_recurring_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    # Version ledger: 18.0 = Odoo version. 1 = Major. Non regressionable code.
    #                 0 = Minor. New features, backwards compatible.
    #                 0 = Patch. Bug fixes.
}
