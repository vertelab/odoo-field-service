{
    'name': "Field Service: Maintenance (Vertel)",
    'version': '18.0.1.0.0',
    'depends': ['fieldservice_maintenance', 'fieldservice_vrtl', 'maintenance'],
    'author': "Vertel Sverige AB",
    'category': 'Field Service',
    'license': 'AGPL-3',
    'description': """
    Field service: Maintenance (Vertel)
    ===================================

    Vertel adaptations on top of fieldservice_maintenance.

    The base module links a maintenance request to a field service order by
    reference. This module adds what Vertel needs in daily operation:

    - Equipment is required on an order created from a maintenance request.
      A technician cannot be dispatched to an unspecified asset.
    - The order inherits the property from the equipment, so the dispatch
      list can be grouped by property.
    - A smart button on the equipment shows its open maintenance requests
      and field service orders in one place.
    - Cancelling a maintenance request does not cancel the order; the order
      keeps its own lifecycle. The link is cleared only on unlink.

    Nothing here changes the two lifecycles. They still live their own lives.
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_equipment_views.xml',
        'views/fieldservice_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
