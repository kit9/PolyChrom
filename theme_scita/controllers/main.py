# -*- coding: utf-8 -*-
# Part of AppJetty. See LICENSE file for full copyright and licensing details.
import re
import math
import json
import os
import base64
import uuid
from lxml import etree, html
from odoo import http, SUPERUSER_ID, fields
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.web_editor.controllers.main import Web_Editor
from odoo.addons.website.controllers.main import Website
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers import main
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.main import TableCompute


class Website(Website):

    @http.route('/update_scss_file', type='http', auth='public', website=True)
    def update_file(self, **kw):
        if kw['write_str']:
            module_str = '/'.join((os.path.realpath(__file__)).split('/')[:-2])
            file_url = module_str + '/static/src/scss/colors/website_' + \
                str(request.website.id) + '_color_picker.scss'
            f = open(module_str + '/static/src/scss/colors/website_' +
                     str(request.website.id) + '_color_picker.scss', 'w+')
            f.write(kw['write_str'])
            context = dict(request.context)
            request.env["ir.qweb"]._get_asset(
                'web.assets_frontend', options=context)
        return None


class Web_Editor(Web_Editor):

    @http.route("/web_editor/save_scss", type="json", auth="user", website=True)
    def save_scss(self, url, bundle_xmlid, content):
        IrAttachment = request.env["ir.attachment"]
        if url != '/theme_scita/static/src/scss/colors/color_picker.scss':
            return super(Web_Editor, self).save_scss(url, bundle_xmlid, content)

        datas = base64.b64encode((content or "\n").encode("utf-8"))
        custom_url = '/theme_scita/static/src/scss/colors/color_picker' + \
            str(request.website.id)+'.scss'

        custom_attachment = self.get_custom_attachment(custom_url)

        if custom_attachment:
            custom_attachment.write({"datas": datas})

        else:
            new_attach = {
                'name': custom_url,
                'type': "binary",
                'mimetype': "text/scss",
                'datas': datas,
                'datas_fname': url.split("/")[-1],
                'url': custom_url,
            }
            new_attach.update(self.save_scss_attachment_hook())

            IrAttachment.create(new_attach)

            IrUiView = request.env["ir.ui.view"]

            def views_linking_url(view):
                return bool(etree.XML(view.arch).xpath("//link[@href='{}']".format(url)))

            view_to_xpath = IrUiView.get_related_views(
                bundle_xmlid, bundles=True).filtered(views_linking_url)

            new_view = {
                'name': custom_url,
                'key': 'web_editor.scss_%s' % str(uuid.uuid4())[:6],
                'mode': "extension",
                'inherit_id': view_to_xpath.id,
                'arch': """
                    <data inherit_id="%(inherit_xml_id)s" name="%(name)s">
                        <xpath expr="//link[@href='%(url_to_replace)s']" position="attributes">
                            <attribute name="href">%(new_url)s</attribute>
                        </xpath>
                    </data>
                """ % {
                    'inherit_xml_id': view_to_xpath.xml_id,
                    'name': custom_url,
                    'url_to_replace': url,
                    'new_url': custom_url,
                }
            }
            new_view.update(self.save_scss_view_hook())
            IrUiView.create(new_view)

        request.env["ir.qweb"].clear_caches()


class ScitaSliderSettings(http.Controller):

    def get_blog_data(self, slider_type):
        slider_header = request.env['blog.slider.config'].sudo().search(
            [('id', '=', int(slider_type))])
        values = {
            'slider_header': slider_header,
            'blog_slider_details': slider_header.collections_blog_post,
        }
        return values

    def get_categories_data(self, slider_id):
        slider_header = request.env['category.slider.config'].sudo().search(
            [('id', '=', int(slider_id))])
        values = {
            'slider_header': slider_header
        }
        values.update({
            'slider_details': slider_header.collections_category,
        })
        return values

    def get_clients_data(self):
        client_data = request.env['res.partner'].sudo().search(
            [('add_to_slider', '=', True), ('website_published', '=', True)])
        values = {
            'client_slider_details': client_data,
        }
        return values

    def get_teams_data(self):
        employee = request.env['hr.employee'].sudo().search(
            [('include_inourteam', '=', 'True')])
        values = {
            'employee': employee,
        }
        return values

    @http.route(
        "/scita_cookie_notice/ok", auth="public", website=True, type='json',
        methods=['POST'])
    def accept_cookies(self):
        http.request.session["accepted_cookies"] = True
        http.request.env['ir.ui.view'].search([
            ('type', '=', 'qweb')
        ]).clear_caches()
        return {'result': 'ok'}

    @http.route(['/theme_scita/blog_get_options'], type='json', auth="public", website=True)
    def scita_get_slider_options(self):
        slider_options = []
        option = request.env['blog.slider.config'].search(
            [('active', '=', True)], order="name asc")
        for record in option:
            slider_options.append({'id': record.id,
                                   'name': record.name})
        return slider_options

    @http.route(['/theme_scita/blog_get_dynamic_slider'], type='http', auth='public', website=True)
    def scita_get_dynamic_slider(self, **post):
        if post.get('slider-type'):
            values = self.get_blog_data(post.get('slider-type'))
            return request.render("theme_scita.theme_scita_blog_slider_view", values)

    @http.route(['/theme_scita/health_blog_get_dynamic_slider'], type='http', auth='public', website=True)
    def health_get_dynamic_slider(self, **post):
        if post.get('slider-type'):
            values = self.get_blog_data(post.get('slider-type'))
            return request.render("theme_scita.health_blog_slider_view", values)

    @http.route(['/theme_scita/second_blog_get_dynamic_slider'], type='http', auth='public', website=True)
    def second_get_dynamic_slider(self, **post):
        if post.get('slider-type'):
            values = self.get_blog_data(post.get('slider-type'))
            return request.render("theme_scita.scita_blog_2_slider_view", values)

    @http.route(['/theme_scita/third_blog_get_dynamic_slider'], type='http', auth='public', website=True)
    def third_get_dynamic_slider(self, **post):
        if post.get('slider-type'):
            values = self.get_blog_data(post.get('slider-type'))
            return request.render("theme_scita.scita_blog_3_slider_view", values)

    @http.route(['/theme_scita/six_blog_get_dynamic_slider'], type='http', auth='public', website=True)
    def six_get_dynamic_slider(self, **post):
        if post.get('slider-type'):
            values = self.get_blog_data(post.get('slider-type'))
            return request.render("theme_scita.scita_blog_6_slider_view", values)

    @http.route(['/theme_scita/forth_blog_get_dynamic_slider'], type='http', auth='public', website=True)
    def forth_get_dynamic_slider(self, **post):
        if post.get('slider-type'):
            values = self.get_blog_data(post.get('slider-type'))
            return request.render("theme_scita.scita_blog_4_slider_view", values)

    @http.route(['/theme_scita/fifth_blog_get_dynamic_slider'], type='http', auth='public', website=True)
    def fifth_get_dynamic_slider(self, **post):
        if post.get('slider-type'):
            values = self.get_blog_data(post.get('slider-type'))
            return request.render("theme_scita.scita_blog_5_slider_view", values)

    @http.route(['/theme_scita/seven_blog_get_dynamic_slider'], type='http', auth='public', website=True)
    def seven_get_dynamic_slider(self, **post):
        if post.get('slider-type'):
            values = self.get_blog_data(post.get('slider-type'))
            return request.render("theme_scita.scita_blog_7_slider_view", values)

    @http.route(['/theme_scita/eight_blog_get_dynamic_slider'], type='http', auth='public', website=True)
    def eight_get_dynamic_slider(self, **post):
        if post.get('slider-type'):
            values = self.get_blog_data(post.get('slider-type'))
            return request.render("theme_scita.scita_blog_8_slider_view", values)

    @http.route(['/theme_scita/blog_image_effect_config'], type='json', auth='public', website=True)
    def scita_product_image_dynamic_slider(self, **post):
        slider_data = request.env['blog.slider.config'].search(
            [('id', '=', int(post.get('slider_type')))])
        values = {
            's_id': str(slider_data.no_of_counts) + '-' + str(slider_data.id),
            'counts': slider_data.no_of_counts,
            'auto_rotate': slider_data.auto_rotate,
            'auto_play_time': slider_data.sliding_speed,
        }
        return values

    # for Client slider
    @http.route(['/theme_scita/get_clients_dynamically_slider'], type='http', auth='public', website=True)
    def get_clients_dynamically_slider(self, **post):
        values = self.get_clients_data()
        return request.render("theme_scita.theme_scita_client_slider_view", values)

    @http.route(['/theme_scita/second_get_clients_dynamically_slider'], type='http', auth='public', website=True)
    def second_get_clients_dynamically_slider(self, **post):
        values = self.get_clients_data()
        return request.render("theme_scita.second_client_slider_view", values)

    @http.route(['/theme_scita/third_get_clients_dynamically_slider'], type='http', auth='public', website=True)
    def third_get_clients_dynamically_slider(self, **post):
        values = self.get_clients_data()
        return request.render("theme_scita.third_client_slider_view", values)

    # our team

    @http.route(['/biztech_emp_data_one/employee_data'], type='http', auth='public', website=True)
    def get_team_one_dynamically_slider(self, **post):
        values = self.get_teams_data()
        return request.render("theme_scita.it_our_team_view", values)

    @http.route(['/biztech_emp_data_two/employee_data'], type='http', auth='public', website=True)
    def get_team_two_dynamically_slider(self, **post):
        values = self.get_teams_data()
        return request.render("theme_scita.our_team_varient_2_view", values)

    @http.route(['/biztech_emp_data_three/employee_data'], type='http', auth='public', website=True)
    def get_team_three_dynamically_slider(self, **post):
        values = self.get_teams_data()
        return request.render("theme_scita.our_team_varient_3_view", values)

    @http.route(['/biztech_emp_data_four/employee_data'], type='http', auth='public', website=True)
    def get_team_four_dynamically_slider(self, **post):
        values = self.get_teams_data()
        return request.render("theme_scita.our_team_varient_4_view", values)

    @http.route(['/biztech_emp_data_five/employee_data'], type='http', auth='public', website=True)
    def get_team_five_dynamically_slider(self, **post):
        values = self.get_teams_data()
        return request.render("theme_scita.our_team_varient_5_view", values)

    @http.route(['/biztech_emp_data_six/employee_data'], type='http', auth='public', website=True)
    def get_team_six_dynamically_slider(self, **post):
        values = self.get_teams_data()
        return request.render("theme_scita.our_team_varient_6_view", values)

    @http.route(['/biztech_emp_data_seven/employee_data'], type='http', auth='public', website=True)
    def get_team_seven_dynamically_slider(self, **post):
        values = self.get_teams_data()
        return request.render("theme_scita.our_team_varient_7_view", values)

    # For Category slider

    @http.route(['/theme_scita/category_get_options'], type='json', auth="public", website=True)
    def category_get_slider_options(self):
        slider_options = []
        option = request.env['category.slider.config'].search(
            [('active', '=', True)], order="name asc")
        for record in option:
            slider_options.append({'id': record.id,
                                   'name': record.name})
        return slider_options

    @http.route(['/theme_scita/category_get_dynamic_slider'], type='http', auth='public', website=True)
    def category_get_dynamic_slider(self, **post):
        if post.get('slider-id'):
            values = self.get_categories_data(post.get('slider-id'))
            return request.render("theme_scita.theme_scita_cat_slider_view", values)

    @http.route(['/theme_scita/second_get_dynamic_cat_slider'], type='http', auth='public', website=True)
    def second_get_dynamic_cat_slider(self, **post):
        if post.get('slider-id'):
            values = self.get_categories_data(post.get('slider-id'))
            return request.render("theme_scita.second_cat_slider_view", values)

    @http.route(['/theme_scita/scita_image_effect_config'], type='json', auth='public', website=True)
    def category_image_dynamic_slider(self, **post):
        slider_data = request.env['category.slider.config'].search(
            [('id', '=', int(post.get('slider_id')))])
        values = {
            's_id': slider_data.name.lower().replace(' ', '-') + '-' + str(slider_data.id),
            'counts': slider_data.no_of_counts,
            'auto_rotate': slider_data.auto_rotate,
            'auto_play_time': slider_data.sliding_speed,
        }
        return values

    # For Product slider
    @http.route(['/theme_scita/product_get_options'], type='json', auth="public", website=True)
    def product_get_slider_options(self):
        slider_options = []
        option = request.env['product.slider.config'].search(
            [('active', '=', True)], order="name asc")
        for record in option:
            slider_options.append({'id': record.id,
                                   'name': record.name})
        return slider_options

    @http.route(['/theme_scita/product_get_dynamic_slider'], type='http', auth='public', website=True)
    def product_get_dynamic_slider(self, **post):
        if post.get('slider-id'):
            slider_header = request.env['product.slider.config'].sudo().search(
                [('id', '=', int(post.get('slider-id')))])
            values = {
                'slider_header': slider_header
            }
            values.update({
                'slider_details': slider_header.collections_products,
            })
            return request.render("theme_scita.theme_scita_product_slider_view", values)

    @http.route(['/theme_scita/product_image_effect_config'], type='json', auth='public', website=True)
    def product_image_dynamic_slider(self, **post):
        slider_data = request.env['product.slider.config'].search(
            [('id', '=', int(post.get('slider_id')))])
        values = {
            's_id': slider_data.name.lower().replace(' ', '-') + '-' + str(slider_data.id),
            'counts': slider_data.no_of_counts,
            'auto_rotate': slider_data.auto_rotate,
            'auto_play_time': slider_data.sliding_speed,
        }
        return values

    # For multi product slider
    @http.route(['/theme_scita/product_multi_get_options'], type='json', auth="public", website=True)
    def product_multi_get_slider_options(self):
        slider_options = []
        option = request.env['multi.slider.config'].sudo().search(
            [('active', '=', True)], order="name asc")
        for record in option:
            slider_options.append({'id': record.id,
                                   'name': record.name})
        return slider_options

    @http.route(['/retial/product_multi_get_dynamic_slider'], type='http', auth='public', website=True)
    def retail_multi_get_dynamic_slider(self, **post):
        context, pool = dict(request.context), request.env
        if post.get('slider-type'):
            slider_header = request.env['multi.slider.config'].sudo().search(
                [('id', '=', int(post.get('slider-type')))])

            if not context.get('pricelist'):
                pricelist = request.website.get_current_pricelist()
                context = dict(request.context, pricelist=int(pricelist))
            else:
                pricelist = pool.get('product.pricelist').browse(
                    context['pricelist'])

            context.update({'pricelist': pricelist.id})
            from_currency = pool['res.users'].sudo().browse(
                SUPERUSER_ID).company_id.currency_id
            to_currency = pricelist.currency_id

            def compute_currency(price): return pool['res.currency']._convert(
                price, from_currency, to_currency, fields.Date.today())
            values = {
                'slider_details': slider_header,
                'slider_header': slider_header,
                'compute_currency': compute_currency,
            }
            return request.render("theme_scita.scita_multi_cat_slider_view", values)

    @http.route(['/fashion/fashion_product_multi_get_dynamic_slider'], type='http', auth='public', website=True)
    def fashion_multi_get_dynamic_slider(self, **post):
        context, pool = dict(request.context), request.env
        if post.get('slider-type'):
            slider_header = request.env['multi.slider.config'].sudo().search(
                [('id', '=', int(post.get('slider-type')))])

            if not context.get('pricelist'):
                pricelist = request.website.get_current_pricelist()
                context = dict(request.context, pricelist=int(pricelist))
            else:
                pricelist = pool.get('product.pricelist').browse(
                    context['pricelist'])

            context.update({'pricelist': pricelist.id})
            from_currency = pool['res.users'].sudo().browse(
                SUPERUSER_ID).company_id.currency_id
            to_currency = pricelist.currency_id

            def compute_currency(price): return pool['res.currency']._convert(
                price, from_currency, to_currency, fields.Date.today())
            values = {
                'slider_details': slider_header,
                'slider_header': slider_header,
                'compute_currency': compute_currency,
            }
            return request.render("theme_scita.fashion_multi_cat_slider_view", values)

    @http.route(['/theme_scita/product_multi_image_effect_config'], type='json', auth='public', website=True)
    def product_multi_product_image_dynamic_slider(self, **post):
        slider_data = request.env['multi.slider.config'].sudo().search(
            [('id', '=', int(post.get('slider_type')))])
        values = {
            's_id': slider_data.no_of_collection + '-' + str(slider_data.id),
            'counts': slider_data.no_of_collection,
            'auto_rotate': slider_data.auto_rotate,
            'auto_play_time': slider_data.sliding_speed,
            'rating_enable': slider_data.is_rating_enable
        }
        return values


class ScitaShop(WebsiteSale):

    @http.route(['/shop/pager_selection/<model("product.per.page.no"):pl_id>'], type='http', auth="public", website=True)
    def product_page_change(self, pl_id, **post):
        request.session['default_paging_no'] = pl_id.name
        main.PPG = pl_id.name
        return request.redirect('/shop' or request.httprequest.referrer)

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>''',
        '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>/page/<int:page>''',
        '''/shop/brands'''
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, brands=None, **post):
        if request.env['website'].sudo().get_current_website().theme_id.name == 'theme_scita':
            add_qty = int(post.get('add_qty', 1))
            if category:
                category = request.env['product.public.category'].search(
                    [('id', '=', int(category))], limit=1)
                if not category or not category.can_access_from_current_website():
                    raise NotFound()
            if brands:
                req_ctx = request.context.copy()
                req_ctx.setdefault('brand_id', int(brands))
                request.context = req_ctx
            result = super(ScitaShop, self).shop(
                page=page, category=category, search=search, ppg=ppg, **post)

            page_no = request.env['product.per.page.no'].sudo().search(
                [('set_default_check', '=', True)])
            if page_no:
                ppg = page_no.name
            else:
                ppg = main.PPG

            attrib_list = request.httprequest.args.getlist('attrib')
            attrib_values = [[int(x) for x in v.split("-")]
                             for v in attrib_list if v]
            attributes_ids = {v[0] for v in attrib_values}
            attrib_set = {v[1] for v in attrib_values}

            domain = self._get_search_domain(search, category, attrib_values)

            pricelist_context, pricelist = self._get_pricelist_context()

            request.context = dict(
                request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

            url = "/shop"
            if search:
                post["search"] = search
            if post:
                request.session.update(post)

            Product = request.env['product.template'].with_context(
                bin_size=True)

            Category = request.env['product.public.category']
            search_categories = False
            if search:
                categories = Product.search(domain).mapped('public_categ_ids')
                search_categories = Category.search(
                    [('id', 'parent_of', categories.ids)] + request.website.website_domain())
                categs = search_categories.filtered(lambda c: not c.parent_id)
            else:
                categs = Category.search(
                    [('parent_id', '=', False)] + request.website.website_domain())

            parent_category_ids = []
            prevurl = request.httprequest.referrer
            if prevurl:
                if not re.search('/shop', prevurl, re.IGNORECASE):
                    request.session['pricerange'] = ""
                    request.session['min1'] = ""
                    request.session['max1'] = ""
                    request.session['curr_category'] = ""

            session = request.session
            cate_for_price = None
            if category:
                url = "/shop/category/%s" % slug(category)
                cate_for_price = int(category)
                parent_category_ids = [category.id]
                current_category = category
                while current_category.parent_id:
                    parent_category_ids.append(current_category.parent_id.id)
                    current_category = current_category.parent_id
            brand_list = request.httprequest.args.getlist('brand')
            brand_set = set([int(v) for v in brand_list])
            if brand_list:
                brandlistdomain = list(map(int, brand_list))
                domain += [('product_brand_id', 'in', brandlistdomain)]
                bran = []
                brand_obj = request.env['product.brands'].sudo().search(
                    [('id', 'in', brandlistdomain)])
                if brand_obj:
                    for vals in brand_obj:
                        if vals.name not in bran:
                            bran.append((vals.name, vals.id))
                    if bran:
                        request.session["brand_name"] = bran
            if not brand_list:
                request.session["brand_name"] = ''

            is_price_slider = request.env.ref(
                'theme_scita.scita_price_slider_layout')
            if is_price_slider:
                # For Price slider

                is_discount_hide = True if request.website.get_current_pricelist(
                ).discount_policy == 'with_discount' else False

                product_slider_ids = []
                asc_product_slider_ids = Product.search(
                    domain, limit=1, order='list_price')
                desc_product_slider_ids = Product.search(
                    domain, limit=1, order='list_price desc')
                if asc_product_slider_ids:
                    product_slider_ids.append(
                        asc_product_slider_ids.website_price if is_discount_hide else asc_product_slider_ids.list_price)
                if desc_product_slider_ids:
                    product_slider_ids.append(
                        desc_product_slider_ids.website_price if is_discount_hide else desc_product_slider_ids.list_price)

                if product_slider_ids:
                    if post.get("range1") or post.get("range2") or not post.get("range1") or not post.get("range2"):
                        range1 = min(product_slider_ids)
                        range2 = max(product_slider_ids)
                        result.qcontext['range1'] = math.floor(range1)
                        result.qcontext['range2'] = math.ceil(range2)

                    if request.session.get('pricerange'):
                        if cate_for_price and request.session.get('curr_category') and request.session.get('curr_category') != float(cate_for_price):
                            request.session["min1"] = math.floor(range1)
                            request.session["max1"] = math.ceil(range2)

                    if session.get("min1") and session["min1"]:
                        post["min1"] = session["min1"]
                    if session.get("max1") and session["max1"]:
                        post["max1"] = session["max1"]
                    if range1:
                        post["range1"] = range1
                    if range2:
                        post["range2"] = range2
                    if range1 == range2:
                        post['range1'] = 0.0

                    if request.session.get('min1') or request.session.get('max1'):
                        domain += [('list_price', '>=', float(request.session.get('min1'))),
                                   ('list_price', '<=', float(request.session.get('max1')))]
                        request.session["pricerange"] = str(
                            request.session['min1']) + "-To-" + str(request.session['max1'])

                    if session.get('min1') and session['min1']:
                        result.qcontext['min1'] = session["min1"]
                        result.qcontext['max1'] = session["max1"]
            if cate_for_price:
                request.session['curr_category'] = float(cate_for_price)
            if request.session.get('default_paging_no'):
                ppg = int(request.session.get('default_paging_no'))
            keep = QueryURL('/shop', category=category and int(category),
                            search=search, attrib=attrib_list, order=post.get('order'))
            product_count = Product.search_count(domain)
            pager = request.website.pager(
                url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)

            products = Product.search(
                domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

            ProductAttribute = request.env['product.attribute']
            if products:
                # get all products without limit
                selected_products = Product.search(domain, limit=False)
                attributes = ProductAttribute.search([('attribute_line_ids.value_ids', '!=', False), (
                    'attribute_line_ids.product_tmpl_id', 'in', selected_products.ids)])
            else:
                attributes = ProductAttribute.browse(attributes_ids)

            compute_currency = self._get_compute_currency(
                pricelist, products[:1])

            result.qcontext.update({'search_count': product_count,
                                    'products': products,
                                    'category': category,
                                    'categories': categs,
                                    'attributes': attributes,
                                    'compute_currency': compute_currency,
                                    'pager': pager,
                                    'keep': keep,
                                    'add_qty': add_qty,
                                    'search': search,
                                    'pricelist': pricelist,
                                    'brand_set': brand_set,
                                    'bins': TableCompute().process(products, ppg),
                                    'parent_category_ids': parent_category_ids,
                                    'search_categories_ids': search_categories and search_categories.ids,
                                    'domain': domain})
            return result
        else:
            return super(ScitaShop, self).shop(page=page, category=category, search=search, ppg=ppg, **post)

    def get_brands_data(self, product_count, product_label):
        keep = QueryURL('/shop/get_it_brand', brand_id=[])
        value = {
            'website_brands': False,
            'brand_header': False,
            'keep': keep
        }
        if product_count:

            brand_data = request.env['product.brands'].sudo().search(
                [('active', '=', True)], limit=int(product_count))
            if brand_data:
                value['website_brands'] = brand_data
        if product_label:
            value['brand_header'] = product_label
        return value

    @http.route(['/shop/get_brand_slider'],
                type='http', auth='public', website=True)
    def get_brand_slider(self, **post):
        values = self.get_brands_data(
            post.get('product_count'), post.get('product_label'))
        return request.render(
            "theme_scita.retial_brand_snippet_1", values)

    @http.route(['/shop/get_box_brand_slider'],
                type='http', auth='public', website=True)
    def get_box_brand_slider(self, **post):
        values = self.get_brands_data(
            post.get('product_count'), post.get('product_label'))
        return request.render(
            "theme_scita.box_brand_snippet_4", values)

    @http.route(['/shop/get_it_brand'],
                type='http', auth='public', website=True)
    def get_it_brand(self, **post):
        values = self.get_brands_data(
            post.get('product_count'), post.get('product_label'))
        return request.render(
            "theme_scita.it_brand_snippet_1", values)

    @http.route('/update_my_wishlist', type="http", auth="public", website=True)
    def qv_update_my_wishlist(self, **kw):
        if kw['prod_id']:
            self.add_to_wishlist(product_id=int(kw['prod_id']))
        return
