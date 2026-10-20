{
    'name': 'Field Service: Project (Vertel)',
    'version': '18.0.1.0.0',
    'category': 'Field Service',
    'summary': 'Project integration for field service orders (Vertel fork)',
    'description': """
Field Service: Project (Vertel)
===============================

Compatibility bridge for the Vertel field service fork.

In the OCA field service stack, ``fieldservice_project`` adds the
project integration: a field service order is backed by a
``project.task`` so that timesheets, planning and billing can hang off
the same record.

The Vertel fork (``fieldservice_vrtl``) builds this in rather than
adding it:

* ``fieldservice_vrtl`` already depends on ``project``.
* ``fieldservice.order`` uses ``_inherits = {'project.task': 'task_id'}``,
  so every order *is* a project task with ``task_id`` as the link.

This module exists so that modules written against the OCA name
(``fieldservice_project``) can declare a dependency that resolves in a
Vertel installation. It adds no models, fields or views of its own — the
functionality is already present in ``fieldservice_vrtl``.

Do not add code here. If project integration needs to change, change it
in ``fieldservice_vrtl``.
    """,
    'author': 'Vertel Sverige AB',
    'maintainer': 'Vertel Sverige AB',
    'license': 'AGPL-3',
    'repository': 'https://github.com/vertelab/odoo-field-service',
    'website': 'https://vertel.se/apps/odoo-field-service/fieldservice_project_vrtl',
    'depends': [
        'fieldservice_vrtl',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    # Version ledger: 18.0 = Odoo version. 1 = Major. Non regressionable code.
    #                 0 = Minor. New features, backwards compatible.
    #                 0 = Patch. Bug fixes.
}
