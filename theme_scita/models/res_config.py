# -*- coding: utf-8 -*-
# Part of AppJetty. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class CustomResConfiguration(models.TransientModel):
    """ Inherit the base settings to add favicon. """
    _inherit = 'res.config.settings'

    header_logo = fields.Binary(
        'Header Logo', related='website_id.header_logo', readonly=False)
    footer_logo = fields.Binary(
        'Footer Logo', related='website_id.footer_logo', readonly=False)
    is_cookie = fields.Boolean(related='website_id.is_cookie', readonly=False)
    msg_cookie = fields.Text(related='website_id.msg_cookie', readonly=False)
    msg_button = fields.Char(related='website_id.msg_button', readonly=False)
    msg_position = fields.Selection(related='website_id.msg_position',
                                    default='top',
                                    string="Message Position", readonly=False)
