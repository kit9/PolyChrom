# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# 

from odoo import api, exceptions, fields, models


class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'

    print_operation_ids = fields.Many2many('print.operation',
                                           compute='compute_print_operation')
    has_print_operation = fields.Boolean('Has print operations',
                                         compute='compute_print_operation')

    @api.multi
    def compute_print_operation(self):
        for po in self:
            po.print_operation_ids = self.env['print.operation'].search([
                ('print_on', '=', 'stock_pack_operation_manual'),
                ('picking_type_ids', 'in', po.picking_id.picking_type_id.id)
            ])
            po.has_print_operation = True if po.print_operation_ids else False

    @api.multi
    def print_sticker_once(self):
        self.ensure_one()
        for lot in self.pack_lot_ids:
            lot.print_stickers()
        return {
            "type": "ir.actions.do_nothing",
        }

    @api.multi
    def print_sticker_quantity(self):
        self.ensure_one()
        for lot in self.pack_lot_ids:
            lot.print_stickers(lot.qty)
        return {
            "type": "ir.actions.do_nothing",
        }


class StockPackOperationLot(models.Model):
    _inherit = 'stock.pack.operation.lot'

    @api.multi
    def print_stickers(self, qty=1):
        self.ensure_one()
        for print_op in self.operation_id.print_operation_ids:
            print_op.run_code(self, qty, self.id)
