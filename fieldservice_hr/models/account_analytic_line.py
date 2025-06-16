from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    fieldservice_order_line_id = fields.Many2one('fieldservice.order.line',domain=lambda self: self._get_fieldservice_order_line_domain())
    
    def _get_fieldservice_order_line_domain(self):
        # Return your domain as a list of tuples
        order_id = self.env['fieldservice.order'].search([('task_id','=',self.task_id.id)])
        valid_fieldservice_order_lines = self.env['fieldservice.order.line'].search([('order_id','=',order_id.id)])
        domain = [
            # Example: Only lines with status 'open'
            ('id', 'in', valid_fieldservice_order_lines.ids),
            # Add more complex logic as needed
        ]
        _logger.warning("_get_fieldservice_order_line_domain"*100)
        _logger.warning(f"{domain=}")
        return domain
    
    @api.depends('fieldservice_order_line_id')
    def set_task_fieldservice(self):
        for line in self:
            line.task_id = line.order_id.task_id
            line.task_id = line.order_id.task_id.project_id
    
    @api.model_create_multi
    def create(self, vals_list):
        default_project_id = int(self.env['ir.config_parameter'].sudo().get_param('fieldservice.default_project_id') or 0)
        for vals in vals_list:
            if vals.get('fieldservice_order_line_id') and not vals.get('task_id'):
               fieldservice_line = self.env['fieldservice.order.line'].browse(vals.get('fieldservice_order_line_id'))
               vals['task_id'] = fieldservice_line.order_id.task_id.id
        res = super(AccountAnalyticLine, self).create(vals_list)
        return res
            
    # ~ @api.depends('task_id'):
    # ~ def set_task_fieldservice(self)
        # ~ for line in self:
            # ~ line.task_id = line.order_id.task_id
            # ~ line.task_id = line.order_id.task_id.project_id
