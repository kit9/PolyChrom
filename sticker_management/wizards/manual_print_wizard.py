# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr
import urllib2
import math
import urllib, json
import logging

_logger = logging.getLogger(__name__)


class ManualPrintWizardLine(models.TransientModel):
    _name = 'manual.print.wizard.line'

    parameter_name = fields.Char(string='Name')
    parameter_value = fields.Char(string='Value')

    wizard_id = fields.Many2one('manual.print.wizard', 'parameter_line_ids')


class ManualPrintWizard(models.TransientModel):
    _name = 'manual.print.wizard'

    print_operation_id = fields.Many2one('print.operation',
                                         string='Print Operation')

    bartender_host_ids = fields.Many2many(
        related='print_operation_id.bartender_host_ids')

    print_qty = fields.Integer(string='Quantity to print', default=1)
    print_template_name = fields.Char(
        string='Name of the bartender template',
        required=True, related='print_operation_id.print_template_name')

    parameter_line_ids = fields.One2many('manual.print.wizard.line',
                                         'wizard_id',
                                         string='Parameters')

    @api.multi
    def print_sticker(self):

        if not self.bartender_host_ids:
            raise ValidationError('Please Configure a Bartender Host/port')
        for bartender in self.bartender_host_ids:
            url = 'http://%s:%s/Integration/%s/Execute' \
                  % (bartender.host, bartender.port,
                     self.print_operation_id.print_template_name)

            params = {}
            for line in self.parameter_line_ids:
                params[line.parameter_name] = line.parameter_value

            req = urllib2.Request(url)
            req.add_header('Content-Type', 'application/json')

            _logger.info("Printed with url %s and parameters %s" % (
                url, json.dumps(params)))

            try:
                response = urllib2.urlopen(req, json.dumps(params))
                _logger.info(response)
            except urllib2.URLError, ex:
                _logger.info('Exception occured during print: %s' % ex)
