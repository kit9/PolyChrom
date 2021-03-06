# -*- coding: utf-8 -*-
# Part of AppJetty. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class BlogSlider(models.Model):
    _name = 'blog.slider.config'
    _description = 'Blog Slider'

    name = fields.Char(string="Slider name", default='Blogs',
                       help="""Slider title to be displayed on 
                       website like Our Blogs, Latest Blog Post and etc...""",
                       required=True, translate=True)
    active = fields.Boolean(string="Active", default=True)
    no_of_counts = fields.Selection([('1', '1'), ('2', '2'), ('3', '3')], string="Counts",
                                    default='3',
                                    help="No of blogs to be displayed in slider.",
                                    required=True)
    auto_rotate = fields.Boolean(string='Auto Rotate Slider', default=True)
    sliding_speed = fields.Integer(string="Slider sliding speed", default='5000',
                                   help='''Sliding speed of a slider can be set 
                                   from here and it will be in milliseconds.''')
    collections_blog_post = fields.Many2many('blog.post', 'blogpost_slider_rel', 'slider_id',
                                             'post_id',
                                             string="Collections of blog posts", required=True)


class CategorySlider(models.Model):
    _name = 'category.slider.config'
    _description = 'Categories Slider'

    name = fields.Char(string="Slider name", required=True,
                       translate=True,
                       help="""Slider title to be displayed on website
                        like Best Categories, Latest and etc...""")
    active = fields.Boolean(string="Active", default=True)

    collections_category = fields.Many2many('product.public.category',
                                            'theme_scita_category_slider_rel',
                                            'slider_id', 'cat_id',
                                            string="Collections of category")


class MultiSlider(models.Model):
    _name = 'multi.slider.config'
    _description = "Configration of Multi slider"

    name = fields.Char(string="Slider name", default='Trending',
                       required=True, translate=True,
                       help="Slider title to be displayed on website like Best products, Latest and etc...")
    active = fields.Boolean(string="Active", default=True)

    auto_rotate = fields.Boolean(string='Auto Rotate Slider', default=True)
    sliding_speed = fields.Integer(string="Slider sliding speed", default='5000',
                                   help='Sliding speed of a slider can be set from here and it will be in milliseconds.')
    is_rating_enable = fields.Boolean(
        string='Show Product Rating', default=True)
    no_of_collection = fields.Selection([('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
                                        string="No. of collections to show", default='2',
                                        required=True,
                                        help="No of collections to be displayed on slider.")

    label_collection_1 = fields.Char(string="1st collection name", default='First collection',
                                     required=True, translate=True,
                                     help="Collection label to be displayed in website like Men, Women, Kids, etc...")
    collection_1_ids = fields.Many2many('product.template', 'product_slider_collection_1_rel', 'slider_id',
                                        'prod_id',
                                        required=True,
                                        string="1st product collection")

    label_collection_2 = fields.Char(string="2nd collection name", default='Second collection',
                                     required=True, translate=True,
                                     help="Collection label to be displayed in website like Men, Women, Kids, etc...")
    collection_2_ids = fields.Many2many('product.template', 'product_slider_collection_2_rel', 'slider_id',
                                        'prod_id',
                                        required=True,
                                        string="2nd product collection")

    label_collection_3 = fields.Char(string="3rd collection name", default='Third collection', translate=True,
                                     # required=True,
                                     help="Collection label to be displayed in website like Men, Women, Kids, etc...")
    collection_3_ids = fields.Many2many('product.template', 'product_slider_collection_3_rel', 'slider_id',
                                        'prod_id',
                                        # required=True,
                                        string="3rd product collection")

    label_collection_4 = fields.Char(string="4th collection name", default='Fourth collection', translate=True,
                                     # required=True,
                                     help="Collection label to be displayed in website like Men, Women, Kids, etc...")
    collection_4_ids = fields.Many2many('product.template', 'product_slider_collection_4_rel', 'slider_id',
                                        'prod_id',
                                        # required=True,
                                        string="4th product collection")

    label_collection_5 = fields.Char(string="5th collection name", default='Fifth collection', translate=True,
                                     # required=True,
                                     help="Collection label to be displayed in website like Men, Women, Kids, etc...")
    collection_5_ids = fields.Many2many('product.template', 'product_slider_collection_5_rel', 'slider_id',
                                        'prod_id',
                                        # required=True,
                                        string="5th product collection")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    include_inourteam = fields.Boolean(
        string="Enable to make the employee visible in snippet")
    emp_social_twitter = fields.Char(
        string="Twitter account", default="https://twitter.com/Odoo")
    emp_social_facebook = fields.Char(
        string="Facebook account", default="https://www.facebook.com/Odoo")
    emp_social_linkdin = fields.Char(
        string="Linkedin account", default="https://www.linkedin.com/company/odoo")
    emp_description = fields.Text(
        string="Short description about employee", translate=True)

    @api.model
    def create(self, vals):
        if vals.get('include_inourteam') == True:
            vals.update({'website_published': True})
        res = super(HrEmployee, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('include_inourteam') == True:
            vals.update({'website_published': True})
        if vals.get('include_inourteam') == False:
            vals.update({'website_published': False})
        res = super(HrEmployee, self).write(vals)
        return res
