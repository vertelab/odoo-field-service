{
    'name': "Field service: Maintenance",
    'version': '18.0.1.0.1',
    'depends': ['fieldservice_vrtl', 'maintenance'],
    'author': "Vertel Sverige AB",
    'category': 'Field Service',
    'license': 'AGPL-3',
    'description': """
    Field service: Maintenance
    ==========================

    Bridges maintenance requests and field service orders.

    A maintenance request and a field service order are two different
    lifecycles that often concern the same physical work:

    - maintenance.request: new, in progress, repaired, scrapped
    - fieldservice.order: draft, scheduled, en route, in progress, done

    They are linked by reference, never by inheritance. Both models carry
    their own stage, description and user fields, and merging them would
    force one lifecycle onto the other. This module keeps them independent
    and lets a request spawn a dispatchable order when a technician has to
    go on site.

    Equipment is carried over so the technician sees which asset the work
    concerns.
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_request_views.xml',
        'views/fieldservice_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
