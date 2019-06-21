# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models, fields


class MrpProductProduce(models.TransientModel):

    _inherit = 'mrp.product.produce'

    @api.multi
    def do_produce(self):
        val = super(MrpProductProduce, self).do_produce()
        print_operations = \
            self.production_id.picking_type_id.print_operation_ids

        quantity_operations = print_operations.filtered(
            lambda op: op.print_on == 'input_quantity')

        for print_op in quantity_operations:
            print_op.run_code(object_id=self.production_id,
                              quantity=self.product_qty)

        return val


class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    printed_sticker_ids = fields.One2many('printed.sticker',
                                          'mrp_production_id',
                                          string='Printed Stickers')

    has_print_operation = fields.Boolean(string='Has print operation',
                                         compute='compute_print_operation')

    print_operation_ids = fields.Many2many('print.operation',
                                           compute='compute_print_operation')

    @api.multi
    def compute_print_operation(self):
        for op in self:
            op.has_print_operation = False
            op.print_operation_ids = self.env['print.operation'].search([
                ('print_on', '=', 'production_has_lot'),
                ('picking_type_ids', 'in', op.picking_type_id.id)
            ])
            op.has_print_operation = True if op.print_operation_ids else False

    @api.multi
    def print_stickers(self):
        self.ensure_one()
        lots = self.env['stock.move.lots'].search([('move_id', 'in', self.move_finished_ids.ids)])

        for lot in lots:
            for print_op in self.print_operation_ids:
                print_op.run_code(self, lot)

    @api.multi
    def button_mark_done(self):
        val = super(MrpProduction, self).button_mark_done()

        print_operations = \
            self.picking_type_id.print_operation_ids

        quantity_operations = print_operations.filtered(
            lambda op: op.print_on == 'mark_as_done')

        for print_op in quantity_operations:
            print_op.run_code(self, self.product_qty)

        return val


class MrpWorkorder(models.Model):

    _inherit = 'mrp.workorder'

    @api.multi
    def record_production(self):
        self.ensure_one()
        # we store this value because it will be updated by the call to
        # super
        qty_to_print = self.qty_producing
        lot_id = self.final_lot_id
        val = super(MrpWorkorder, self).record_production()

        print_operations = \
            self.production_id.picking_type_id.print_operation_ids

        quantity_operations = print_operations.filtered(
            lambda op: op.print_on == 'workorder_done' and
                       self.operation_id in op.operation_ids)

        for print_op in quantity_operations:
            print_op.run_code(self, qty_to_print, lot_id)

        return val
