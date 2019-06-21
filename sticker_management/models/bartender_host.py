# -*- coding: utf-8 -*-
# © 2018 Antoine Verlant
# © 2018 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class BartenderHost(models.Model):
    _name = 'bartender.host'

    name = fields.Char(string='Name', required=True,
                       helper='Indicate Location')

    host = fields.Char('Host', required=True)
    port = fields.Char('Port', required=True)
