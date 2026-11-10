{
    'name': "Field Service: Accounting (Vertel)",
    'version': '18.0.1.1.1',
    'depends': ['fieldservice_vrtl','hr_timesheet','hr'],
    'author': "Vertel Sverige AB",
    'category': 'Category',
    'license': 'AGPL-3',
    'description': """
    Field Service: Accounting (Vertel)
    ==================================

    Links an invoice line to the field service order it was invoiced from.
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/fieldservice_order_view.xml',
    ],
}
