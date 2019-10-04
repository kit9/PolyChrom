# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class Company(models.Model):
	_inherit = 'res.company'


	serial_no = fields.Integer(default = 0)
	digits_serial_no = fields.Integer(string='Digits :')
	prefix_serial_no = fields.Char(string="Prefix :")

class ProductProductInherit(models.Model):
	_inherit = "product.template"

	digits_serial_no = fields.Integer(string='Digits :')
	prefix_serial_no = fields.Char(string="Prefix :")

class QualityCheckInherit(models.Model):
	_inherit = "quality.check"

	@api.model
	def create(self, values):
		record = super(QualityCheckInherit, self).create(values)
		lot_id = record['lot_id']
		component = record['component_id']
		move_line = record['move_line_id']
		if not lot_id and component and component.tracking != 'none':
			wo = record['workorder_id']
			# this will set the Serial Number
			if component.tracking == 'serial':
				move = wo.production_id.move_raw_ids.filtered(lambda move: move.product_id.id == wo.production_id.bom_id.prev_product_id.id)
				if move_line and move_line.lot_id and move_line.product_id.id == wo.production_id.bom_id.prev_product_id.id:
					record['lot_id'] = move_line.lot_id.id
				elif move and move[0].active_move_line_ids:
					serial_id = move[0].active_move_line_ids.filtered(lambda aml: not aml.lot_produced_id)
					if serial_id:
						record['lot_id'] = serial_id[0].lot_id.id
			else:
				lot_id = self.env['stock.production.lot'].search([('product_id', '=', component.id)], limit=1)
				record['lot_id'] = lot_id.id
		
		return record
			
class MrpBom(models.Model):
	_inherit = 'mrp.bom'
	
	prev_product_id = fields.Many2one('product.product', 'Previous Product Lot/Serial No.', domain=lambda self: self._getfilter())
	
	@api.model
	def _getfilter(self):
		products = []
		if self.bom_line_ids:
			for x in self.bom_line_ids:
				if x.product_tmpl_id.tracking == 'serial':
					products.append(x.product_id.id)
		return [('id', 'in', products)]
	
	@api.onchange('bom_line_ids')
	def bom_line_ids_onchange(self):
		res = {}
		products = []
		if self.bom_line_ids:
			for x in self.bom_line_ids:
				if x.product_tmpl_id.tracking == 'serial':
					products.append(x.product_id.id)
		res['domain']={'prev_product_id':[('id', 'in', products)]}
		return res
	
class MrpProductionInherit(models.Model):
	""" Manufacturing Orders """
	_inherit = 'mrp.production'

	# lot_numbr = fields.Char(string="lot number")

	def do_produce_more(self, produce):
		close = produce.do_produce()
		_logger.info("*** Closing using the following action: %s and %s", self.qty_produced, self.product_qty)
		# next = self.open_produce_product()
		if self.qty_produced >= self.product_qty:
			_logger.info("*** Closing using the following action: %s", close)
			return close
		_logger.info("*** Self Ensure One")
		self.ensure_one()
		
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
		
		_logger.info("*** Line Lot Id: %s as Name %s", produce.lot_id, produce.lot_id.name)
		lot_serial_no = False
		if self.bom_id and self.bom_id.prev_product_id:
			if prefix == False:
				prefix = 'F'

			prev_prod = self.bom_id.prev_product_id.id

			#product_line = produce.produce_line_ids.filtered(lambda x: x.product_id == prev_prod)[0]
			#.search(['&', ('product_produce_id', '=', produce.id), ('product_id', '=', prev_prod)], limit=1)
			move = self.move_raw_ids.filtered(lambda x: x.product_id.id == prev_prod)[0]
			move_line = move.active_move_line_ids.filtered(lambda x: not x.lot_produced_id)

			if move_line:
				#lot_no = prefix+product_line.lot_id.name
				lot_no = prefix+move_line[0].lot_id.name
				serialExists = self.env['stock.production.lot'].search(['&', ('name', '=', lot_no), ('product_id', '=', produce.product_id.id)])
				if not serialExists:
					lot_serial_no = self.env['stock.production.lot'].create({'name' : lot_no, 'product_id':produce.product_id.id})
				else:
					lot_serial_no = serialExists[0]

		# This is the original way
		if lot_serial_no == False:
			if prefix != False:
				lot_no = prefix+no+str(serial_no)
			else:
				lot_no = str(serial_no)
			company.update({'serial_no' : serial_no})
			lot_serial_no = self.env['stock.production.lot'].create({'name' : lot_no,'product_id':self.product_id.id})
		produce.lot_id = lot_serial_no
		_logger.info("*** New Line Lot Id: %s as Name %s", produce.lot_id, produce.lot_id.name)
		_logger.info("*** Produce Line Ids: %s",  produce.produce_line_ids)
		
		reopen_form = produce._reopen_form() #{"type": "ir.actions.do_nothing"}
		#actionXml = self.env.ref('mrp.act_mrp_product_produce').read()
		return reopen_form
	
	def create_custom_lot_no(self):
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
						
		lot_serial_no = False			
			
		if self.bom_id and self.bom_id.prev_product_id:
			if prefix == False:
				prefix = 'F'
				
			prev_prod = self.bom_id.prev_product_id.id
			
			material = self.move_raw_ids.filtered(lambda mat: mat.product_id.id == prev_prod )
			for m in material:
				ln = m.active_move_line_ids.filtered(lambda aml: aml.state == 'assigned' and not aml.lot_produced_id)
				if ln and ln[0] and ln[0].lot_id:
					lot_no = prefix+ln[0].lot_id.name
					serialExists = self.env['stock.production.lot'].search(['&', ('name', '=', lot_no), ('product_id', '=', self.product_id.id)])
					if not serialExists:
						lot_serial_no = self.env['stock.production.lot'].create({'name' : lot_no,'product_id':self.product_id.id})
						break
					else:
						lot_serial_no = serialExists[0]
						break
						
		#The Original Way	
		if not lot_serial_no:
			cnt = 0
			serialExists = False
			while not serialExists and cnt <=20:
				if prefix != False:
					lot_no = prefix+no+str(serial_no)
				else:
					lot_no = str(serial_no)
				serialExists = self.env['stock.production.lot'].search(['&', ('name', '=', lot_no), ('product_id', '=', self.product_id.id)])
				if serialExists:
					serial_no= serial_no + 1
					cnt = cnt + 1
				else:
					break
				
			company.write({'serial_no' : serial_no})
			lot_serial_no = self.env['stock.production.lot'].create({'name' : lot_no,'product_id':self.product_id.id})			
		return lot_serial_no

	def _workorders_create(self, bom, bom_data):
		res = super(MrpProductionInherit, self)._workorders_create(bom,bom_data)
		lot_id = self.create_custom_lot_no()
		for lot in res:
			lot.final_lot_id = lot_id.id
			lot.lot_numbr = lot_id.id
			move = self.move_raw_ids.filtered(lambda move: move.workorder_id.id == lot.id and (move.product_id.id == self.bom_id.prev_product_id.id or move.product_id.tracking == 'lot'))
			qa = self.env['quality.check'].search(['&', ('quality_state', '=', 'none'), ('workorder_id', '=', self.id)], limit=1)
		return res
	
	
class MrpworkorderInherit(models.Model):
	""" Manufacturing Orders """
	_inherit = 'mrp.workorder'

	lot_numbr = fields.Char(string="lot number")
	
	@api.onchange('lot_id')
	def _onchange_lot_id(self):
		if self.production_id.bom_id.prev_product_id:
			prefix = self.product_id.prefix_serial_no
			lot_name = self.lot_id.name
			lotExists = self.env['stock.production.lot'].search(['&', ('name', '=', prefix+lot_name), ('product_id', '=', self.product_id.id)], limit=1)
			if not lotExists:
				lotExists = self.env['stock.production.lot'].create({'name': prefix+lot_name, 'product_id': self.product_id.id})
			self.final_lot_id = lotExists.id
			
	
	#def _create_checks(self):
	#	_logger.info('*** ### Create Override')
		#res = super(MrpworkorderInherit, self)._create_checks()
		#move = self.production_id.move_raw_ids.filtered(lambda move: move.product_id.id == self.production_id.bom_id.prev_product_id.id)
		#
		#if move and move[0].active_move_line_ids:
		#	_logger.info('*** ### Set Lot Number with serial')
		#	self.current_quality_check_id.write({'lot_id': move[0].active_move_line_ids[0].lot_id.id})
		#elif self.current_quality_check_id.component_id == 'lot':
		#	_logger.info('*** ### Set Lot Number with Lot')
		#	lot_id = self.env['stock.production.lot'].search([('product_id', '=', self.current_quality_check_id.component_id.id)], limit=1)
		#	self.current_quality_check_id.write({'lot_id': lot_id.id})
	
		
	@api.multi
	def record_production(self):
		if not self:
			return True
		self.ensure_one()
		if self.qty_producing <= 0:
			raise UserError(_('Please set the quantity you are currently producing. It should be different from zero.'))
		
		if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id and self.move_raw_ids:
			raise UserError(_('You should provide a lot/serial number for the final product.'))
		
		qa = self.env['quality.check'].search(['&', ('quality_state', '=', 'none'), ('workorder_id', '=', self.id)])
	
		# Update quantities done on each raw material line
		# For each untracked component without any 'temporary' move lines,
		# (the new workorder tablet view allows registering consumed quantities for untracked components)
		# we assume that only the theoretical quantity was used
		for move in self.move_raw_ids:
			_logger.info('*** Stock Move Line Ids: %s', move.active_move_line_ids)
			if move.has_tracking == 'none' and (move.state not in ('done', 'cancel')) and move.bom_line_id\
						and move.unit_factor and not move.move_line_ids.filtered(lambda ml: not ml.done_wo):
				rounding = move.product_uom.rounding
				if self.product_id.tracking != 'none':
					qty_to_add = float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding)
					move._generate_consumed_move_line(qty_to_add, self.final_lot_id)
				elif len(move._get_move_lines()) < 2:
					move.quantity_done += float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding)
				else:
					move._set_quantity_done(move.quantity_done + float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding))

		# Transfer quantities from temporary to final move lots or make them final
		for move_line in self.active_move_line_ids:
			# Check if move_line already exists
			if move_line.qty_done <= 0:  # rounding...
				move_line.sudo().unlink()
				continue
			if move_line.product_id.tracking != 'none' and not move_line.lot_id:
				raise UserError(_('You should provide a lot/serial number for a component.'))
			# Search other move_line where it could be added:
			lots = self.move_line_ids.filtered(lambda x: (x.lot_id.id == move_line.lot_id.id) and (not x.lot_produced_id) and (not x.done_move) and (x.product_id == move_line.product_id))
			if lots:
				lots[0].qty_done += move_line.qty_done
				lots[0].lot_produced_id = self.final_lot_id.id
				self._link_to_quality_check(move_line, lots[0])
				move_line.sudo().unlink()
			else:
				move_line.lot_produced_id = self.final_lot_id.id
				move_line.done_wo = True
		self.move_line_ids.filtered(
			lambda move_line: not move_line.done_move and not move_line.lot_produced_id and move_line.qty_done > 0
		).write({
			'lot_produced_id': self.final_lot_id.id,
			'lot_produced_qty': self.qty_producing
		})

		# If last work order, then post lots used
		# TODO: should be same as checking if for every workorder something has been done?
		if not self.next_work_order_id:
			production_move = self.production_id.move_finished_ids.filtered(
								lambda x: (x.product_id.id == self.production_id.product_id.id) and (x.state not in ('done', 'cancel')))
			if production_move.product_id.tracking != 'none':
				move_line = production_move.move_line_ids.filtered(lambda x: x.lot_id.id == self.final_lot_id.id)
				if move_line:
					move_line.product_uom_qty += self.qty_producing
					move_line.qty_done += self.qty_producing
				else:
					location_dest_id = production_move.location_dest_id.get_putaway_strategy(self.product_id).id or production_move.location_dest_id.id
					move_line.create({'move_id': production_move.id,
							 'product_id': production_move.product_id.id,
							 'lot_id': self.final_lot_id.id,
							 'product_uom_qty': self.qty_producing,
							 'product_uom_id': production_move.product_uom.id,
							 'qty_done': self.qty_producing,
							 'workorder_id': self.id,
							 'location_id': production_move.location_id.id,
							 'location_dest_id': location_dest_id,
					})
			else:
				production_move.quantity_done += self.qty_producing

		if not self.next_work_order_id:
			for by_product_move in self._get_byproduct_move_to_update():
					if by_product_move.has_tracking != 'serial':
						values = self._get_byproduct_move_line(by_product_move, self.qty_producing * by_product_move.unit_factor)
						self.env['stock.move.line'].create(values)
					elif by_product_move.has_tracking == 'serial':
						qty_todo = by_product_move.product_uom._compute_quantity(self.qty_producing * by_product_move.unit_factor, by_product_move.product_id.uom_id)
						for i in range(0, int(float_round(qty_todo, precision_digits=0))):
							values = self._get_byproduct_move_line(by_product_move, 1)
							self.env['stock.move.line'].create(values)
		# Update workorder quantity produced
		self.qty_produced += self.qty_producing
		if self.final_lot_id:
			self.final_lot_id.use_next_on_work_order_id = self.next_work_order_id
			self.final_lot_id = False



		# Once a piece is produced, you can launch the next work order
		self._start_nextworkorder()



		# Set a qty producing
		rounding = self.production_id.product_uom_id.rounding
		if float_compare(self.qty_produced, self.production_id.product_qty, precision_rounding=rounding) >= 0:
			self.qty_producing = 0
		elif self.production_id.product_id.tracking == 'serial':
			self._assign_default_final_lot_id()
			self.qty_producing = 1.0
			self._generate_lot_ids()
		else:
			self.qty_producing = float_round(self.production_id.product_qty - self.qty_produced, precision_rounding=rounding)
			self._generate_lot_ids()
			
		new_lot_id = self.production_id.create_custom_lot_no()
		self.lot_numbr = new_lot_id.id
		self.final_lot_id = int(self.lot_numbr)
		
		if self.next_work_order_id and self.production_id.product_id.tracking != 'none':
			self.next_work_order_id._assign_default_final_lot_id()
			
		

		if float_compare(self.qty_produced, self.production_id.product_qty, precision_rounding=rounding) >= 0:
			self.button_finish()
		return True
