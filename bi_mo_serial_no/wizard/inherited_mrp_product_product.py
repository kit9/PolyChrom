# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

import logging
from collections import Counter
from datetime import datetime

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round

_logger = logging.getLogger(__name__)

class MrpProductProduce(models.TransientModel):
	_inherit = 'mrp.product.produce'

	lot_id = fields.Many2one('stock.production.lot', string='Lot',required=False)

	@api.model
	def default_get(self, fields):
		if 'serial' not in fields:
			fields.append('serial')
		if 'production_id' not in fields:
			fields.append('production_id')
		if 'product_tracking' not in fields:
			fields.append('product_tracking')
		if 'produce_line_ids' not in fields:
			fields.append('produce_line_ids')
			
		
		res = super(MrpProductProduce, self).default_get(fields)
		if 'production_id' in res:
			production = self.env['mrp.production'].browse(res['production_id'])
			lot_serial_no = False
			if production and production.bom_id and production.bom_id.prev_product_id:
				prefix = production.product_id.prefix_serial_no
				prev_prod = production.bom_id.prev_product_id.id
				move = production.move_raw_ids.filtered(lambda x: x.product_id.id == prev_prod and x.product_id.tracking != 'none' and x.state not in ('done', 'cancel') and x.bom_line_id)
				
				if move:
					move_line = move[0].move_line_ids.filtered(lambda x: not x.lot_produced_id)
					if move_line:
						lot_no = prefix+move_line[0].lot_id.name
						serialExists = self.env['stock.production.lot'].search(['&', ('name', '=', lot_no), ('product_id', '=', production.product_id.id)])
						if not serialExists:
							lot_serial_no = self.env['stock.production.lot'].create({'name' : lot_no,'product_id':production.product_id.id})
						else:
							lot_serial_no = serialExists[0]
			elif production.product_id.tracking != 'none':
				used_moves = self.env['stock.move.line'].search([('product_id', '=', production.product_id.id)])
				used_lots = [x.lot_id.id for x in used_moves]
				_logger.info('^^^ Default Get, list of used lots: %s', used_lots)
				unused_lots = self.env['stock.production.lot'].search([('id', 'not in', used_lots)])
				_logger.info('^^^ Default Get, list of unused lots: %s', unused_lots)
				if unused_lots:
					_logger.info('^^^ Default Get, use lot: %s', unused_lots[0])
					lot_serial_no = unused_lots[0]
				else:
					lot_serial_no = production.create_custom_lot_no()
					_logger.info('^^^ Default Get, create new lot: %s', lot_serial_no)
			if lot_serial_no:
				res['lot_id'] = lot_serial_no.id
		
		return res
	
	@api.multi
	def _reopen_form(self):
		self.ensure_one()
		return {'type': 'ir.actions.act_window',
		       'res_model': self._name,
		       'res_id': self.id,
		       'view_type': 'form',
		       'view_mode': 'form',
			'context': {'move_line_next': 1},
		       'target': 'new'}
	
	@api.multi
	def do_produce_more(self):
		return self.production_id.do_produce_more(self)

	@api.multi
	def do_produce(self):
		company = self.env['res.company']._company_default_get('mrp.product.produce')
		result = self.env['res.config.settings'].search([],order="id desc", limit=1)

		if result.apply_method == "global":
			digit = result.digits_serial_no
			prefix = result.prefix_serial_no
		else:
			digit = self.product_id.digits_serial_no
			prefix = self.product_id.prefix_serial_no
			
		serial_no = company.serial_no + 1
		serial_no_digit=len(str(company.serial_no))

		diffrence = abs(serial_no_digit - digit)
		if diffrence > 0:
			no = "0"
			for i in range(diffrence-1) :
				no = no + "0"
		else :
			no = ""
			
		# Nothing to do for lots since values are created using default data (stock.move.lots)
		quantity = self.product_qty
		if float_compare(quantity, 0, precision_rounding=self.product_uom_id.rounding) <= 0:
			raise UserError(_("The production order for '%s' has no quantity specified") % self.product_id.display_name)
		for move in self.production_id.move_raw_ids:
			# TODO currently not possible to guess if the user updated quantity by hand or automatically by the produce wizard.
			if move.product_id.tracking == 'none' and move.state not in ('done', 'cancel') and move.unit_factor:
				rounding = move.product_uom.rounding
				if self.product_id.tracking != 'none':
					qty_to_add = float_round(quantity * move.unit_factor, precision_rounding=rounding)
					move._generate_consumed_move_line(qty_to_add, self.lot_id)
				else:
					move.quantity_done += float_round(quantity * move.unit_factor, precision_rounding=rounding)
		for move in self.production_id.move_finished_ids:
			if move.product_id.tracking == 'none' and move.state not in ('done', 'cancel'):
				rounding = move.product_uom.rounding
				if move.product_id.id == self.production_id.product_id.id:
					move.quantity_done += float_round(quantity, precision_rounding=rounding)
				elif move.unit_factor:
					# byproducts handling
					move.quantity_done += float_round(quantity * move.unit_factor, precision_rounding=rounding)
		self.check_finished_move_lots()
		if self.production_id.state == 'confirmed':
			self.production_id.write({
				'state': 'progress',
				'date_start': datetime.now(),
			})
		return {'type': 'ir.actions.act_window_close'}

