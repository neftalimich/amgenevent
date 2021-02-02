# -*- coding: utf-8 -*-
# from odoo import http


# class Amgenevent(http.Controller):
#     @http.route('/amgenevent/amgenevent/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/amgenevent/amgenevent/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('amgenevent.listing', {
#             'root': '/amgenevent/amgenevent',
#             'objects': http.request.env['amgenevent.amgenevent'].search([]),
#         })

#     @http.route('/amgenevent/amgenevent/objects/<model("amgenevent.amgenevent"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('amgenevent.object', {
#             'object': obj
#         })
