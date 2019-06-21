# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockPickingType(models.Model):

    _inherit = 'stock.picking.type'

    print_operation_ids = fields.Many2many('print.operation',
                                           string='Print Operations')
