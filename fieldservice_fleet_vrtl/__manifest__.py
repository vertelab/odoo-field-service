{
    'name': 'Field Service - Fleet (Vertel)',
    'version': '18.0.1.0.0',
    'category': 'Field Service',
    'summary': 'Link field service teams to fleet vehicles',
    'description': """
Field Service - Fleet
=====================

Bridge module between ``fieldservice_vrtl`` and Odoo's ``fleet`` app.

A field service team can be assigned one or more vehicles. The vehicle is
optional: a team may be a work crew without a dedicated van, a competence
group, or a single technician.

The module installs itself as soon as both ``fieldservice_vrtl`` and
``fleet`` are installed, so the base field service module stays free of
the fleet dependency.
""",
    'author': 'Vertel Sverige AB',
    'maintainer': 'Vertel Sverige AB',
    'website': 'https://www.vertel.se',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'license': 'AGPL-3',
    'depends': [
        'fieldservice_vrtl',
        'fleet',
    ],
    'data': [
        'views/fieldservice_team_views.xml',
        'views/fleet_vehicle_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': True,
}
