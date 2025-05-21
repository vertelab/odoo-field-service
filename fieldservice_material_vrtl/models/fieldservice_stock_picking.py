from odoo import models, fields, api

class FieldServiceOrderLine(models.Model):
    _inherit = 'fieldservice.order.line'

    def action_create_stock_picking(self):
        """Create stock pickings for used and requested materials."""
        for line in self:
            # Create picking for used materials (outgoing)
            if line.used_material_ids:
                self._create_stock_picking(line.used_material_ids, picking_type='outgoing')

            # Create picking for requested materials (incoming)
            if line.requested_material_ids:
                self._create_stock_picking(line.requested_material_ids, picking_type='incoming')
        

    def _create_stock_picking(self, material_lines, picking_type):
        """Helper method to create stock pickings."""
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']

        # Prepare Picking Data
        picking_vals = {
            'partner_id': self.order_id.partner_id.id if self.order_id.partner_id else False,
            'location_id': self.env.ref('stock.stock_location_stock').id,  # Default source location
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id if picking_type == 'outgoing'
                else self.env.ref('stock.stock_location_stock').id
            ),
            'picking_type_id': self.env.ref(f'stock.picking_type_{picking_type}').id,
            'origin': self.order_id.name,
        }
        picking = StockPicking.create(picking_vals)

        # Create Stock Moves for Each Material Line
        for line in material_lines:
            move_vals = {
                'picking_id': picking.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_id.uom_id.id,
                'name': line.product_id.name,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
            }
            StockMove.create(move_vals)

        return picking
