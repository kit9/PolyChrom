# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo.exceptions import ValidationError
import urllib2
import math
import urllib, json
import logging
import yaml

_logger = logging.getLogger(__name__)

DEFAULT_PARAMS = '''#Insert a python dictionnay with all the needed parameters
# you can use 'o' which is the mrp.production object. If you want to print its
# ID, you could add the following to the dictionnary:'production_id': o.id
# Example:
# params = {
#     'product': 'product_name',
#     'price': 125,
#     'barcode': 123456789,
# }
'''


class PrintOperation(models.Model):

    _name = 'print.operation'

    name = fields.Char(string='Name')
    params = fields.Text(string='Parameters',
                         default=DEFAULT_PARAMS)

    print_qty = fields.Integer(string='Quantity to print', default=1)
    print_on = fields.Selection([('mark_as_done', 'Mark as Done'),
                                 ('input_quantity', 'Quantity Input'),
                                 ('workorder_done', 'Work Order is Done'),
                                 ('stock_pack_operation_manual',
                                  'Stock Pack Operation (manual click)'),
                                 ('production_has_lot', 'Production has lots')],
                                required=True, string='Print on')
    print_template_name = fields.Char(string='Name of the bartender template',
                                      required=True)

    object = fields.Selection([('mrp_production', 'MRP Production'),
                               ('products', 'MRP Production Product'),
                               ('mrp_workorder', 'MRP Work Order'),
                               ('stock_pack_operation', 'Stock Pack Operation')],
                              string='Object', required=True)

    operation_ids = fields.Many2many('mrp.routing.workcenter',
                                     string='On operations')

    picking_type_ids = fields.Many2many('stock.picking.type',
                                        string='Picking Type')

    bartender_host_ids = fields.Many2many(
        'bartender.host', relation='print_operation_bartender_rel',
        column1='operation_id', column2='bartender_id',
        string='Bartenders', required=True)

    @api.constrains('params')
    def _check_params(self):
        for action in self.filtered('params'):
            msg = test_python_expr(expr=action.params.strip(), mode='eval')
            if msg:
                raise ValidationError(msg)

    @api.multi
    def test_print(self):
        self.ensure_one()

        if not self.bartender_host_ids:
            raise ValidationError(_('Please Configure at least'
                                  ' one Bartender Server'))
        for bartender in self.bartender_host_ids:
            url = 'http://%s:%s/Integration/%s/Execute' % (
                bartender.host, bartender.port, self.print_template_name)
            try:
                urllib2.urlopen(url).read()
            except urllib2.URLError, ex:
                _logger.info('Exception occured during test of a print: %s URL--%s' % (ex, url) )
                raise exceptions.UserError("Test returned an error : %s" % ex.reason)


    @api.multi
    def run_code(self, object_id=False, quantity=1, final_lot_id=False,
                 pack_lot_id=False):
        self.ensure_one()

        if not self.bartender_host_ids:
            raise ValidationError(_('Please Configure at least'
                                    ' one Bartender Server'))

        elif self.object == 'products':
            object = object_id.move_finished_ids
        else:
            object = object_id

        params = {}
        safe_eval(self.params.strip(),
                  {'o': object,
                   'params': params,
                   'final_lot_id': final_lot_id},
                  mode='eval', nocopy=True)

        # adding the total quantity to print to the parameter
        params['total_quantity'] = int(quantity * self.print_qty)

        for bartender in self.bartender_host_ids:
            self.print_product(
                bartender.host, bartender.port, params, object_id)

    @api.multi
    def print_product(self,  host, port, params, object_id):
        url = 'http://%s:%s/Integration/%s/Execute' \
              % (host, port, self.print_template_name)
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')

        self.env['printed.sticker'].create({
            'template_name': self.print_template_name,
            'json_params': json.dumps(params),
            'date_printed': fields.Datetime.now(),
            'mrp_production_id': object_id.id if
                object_id._name == 'mrp.production' else False,
            'stock_picking_id': object_id.operation_id.picking_id.id if
                object_id._name == 'stock.pack.operation.lot' else False,
            'bartender_host_id': [(6, 0, self.bartender_host_ids.ids)]
        })
        _logger.info("Printed with url %s and parameters %s" % (
            url, json.dumps(params)))

        try:
            response = urllib2.urlopen(req, json.dumps(params))
            _logger.info(response)
        except urllib2.URLError, ex:
            _logger.info('Exception occured during print: %s' % ex)

    @api.multi
    def manual_print(self):
        self.ensure_one()
        params = self.params.strip().split("params.update(", 1)[1][:-1]
        param_dict = yaml.load(params)
        manual_print_lines = []

        for key, value in param_dict.iteritems():
            manual_print_lines.append((0, 0, {
                'parameter_name': key,
                'parameter_value': value,
            }))

        return {
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref(
                'sticker_management.manual_print_form').id,
            'name': 'Manual Print',
            'target': 'new',
            'res_model': 'manual.print.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'context': {
                'default_print_operation_id': self.id,
                'default_parameter_line_ids': manual_print_lines,
            },
        }
