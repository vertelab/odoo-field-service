from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    price_per_hour = fields.Float(
        string="Price per Hour",
        help="Hourly rate billed to the customer. Odoo 18 has no "
             "price_unit on analytic lines, so the rate is kept here and "
             "copied onto the invoice line.",
    )
    time_start = fields.Float(string="Start Time")
    time_end = fields.Float(string="End Time")

    def write(self, vals):
        if 'time_start' in vals or 'time_end' in vals:
            for record in self:
                start = vals.get('time_start', record.time_start)
                end = vals.get('time_end', record.time_end)
                if start and end:
                    vals = dict(vals, unit_amount=end - start)
                    break
        return super().write(vals)
