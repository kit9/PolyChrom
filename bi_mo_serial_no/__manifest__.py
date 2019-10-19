# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Auto Generate serial/lot number from Manufacturing order in odoo',
    'version': '12.0.0.1',
    'category': 'Manufacturing',
    "author": "BrowseInfo",
    'sequence': 15,
    'summary': 'This module helps to automatically generate serial and lot number from the Manufacturing Order.',
    'description': """ Generate serial/lot number based from MO in odoo
    Manufacturing Auto Generate serial number from Manufacturing order, Generate serial/lot number based on MO in odoo , Automatic Generation of lot number from Manufacturing order
    Manufacturing Auto Generate lot number from Manufacturing order , Manufacturing order based serial/lot number , Manufacturing order Generate serial/lot number in odoo
    Manufacturing Automatic Generate serial number from Manufacturing order, Automatic Generate serial number basedon Manufacturing order , Generate serial number from work order in odoo,
	
    Manufacturing Automatic Generate lot number from Manufacturing order, Generate lot number based upon workorder , create lot number based upon workorder , allocate lot number from work order , 
	
Generate serial number from Manufacturing order , Generate serial number in Manufacturing in odoo , lot number in manufacturing order 
    Manufacturing order Auto Generate serial number from MO
    Manufacturing order Auto Generate lot number from MO
    Manufacturing order Automatic Generate serial number from MO
    Manufacturing order Automatic Generate lot number from MO
    manufacturing serial number generate
    manufacturing lot number generate
    manufacturing serial tracibility
    Generate serial/lot number in Manufacturing order
    Generate serial/lot number in MO
    Generate serial number in mo
    Generate lot number in mo
    serial/lot number in Manufacturing order
    lot number in manufacturing order 
    serial number in Manufacturing order

    auto serial number generation from manufacturing

        Manufacturing Auto generation serial number from Manufacturing order
    Manufacturing Auto generation lot number from Manufacturing order
    Manufacturing Automatic generation serial number from Manufacturing order
    Manufacturing Automatic generation lot number from Manufacturing order


    """,
    'website': 'www.browseinfo.in',
    'depends': ['base','mrp','stock', 'sale', 'delivery'],
    'data': [   'wizard/inherited_mrp_product_product_views.xml',
                'views/res_config_setting_views.xml',
                'views/report_assets_common.xml'
                ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    "price": 29.00,
    "currency": 'EUR',
    "live_test_url":'https://youtu.be/RQ9bi15U3ko',
    "images":['static/description/Banner.png'],
}
