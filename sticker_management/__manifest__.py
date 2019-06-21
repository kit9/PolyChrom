# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Sticker and Printer management',
    'category': 'sale',
    'summary': 'Allow the configuration of sticker printer',
    'website': 'https://www.niboo.be',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'description': """
This module allows the user to define a configuration that will allow him to print stickers from a bartender webservice
        """,
    'author': 'Niboo',
    'depends': [
        'stock',
        'mrp',
    ],
    'data': [
        'views/manual_print_wizard.xml',
        'views/printed_stickers.xml',
        'views/bartender_host.xml',
        'views/print_operation.xml',
        'views/stock_picking_type.xml',
        'views/stock_pack_operation.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
