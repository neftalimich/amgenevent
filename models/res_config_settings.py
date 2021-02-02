# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_event_maximum_per_day = fields.Selection([
        ('0', 'Sin Límite'),
        ('5', '5 Eventos'),
        ('7', '7 Eventos'),
        ('10', '10 Eventos'),
        ('15', '15 Eventos'),
        ('20', '20 Eventos'),
    ], string='Límite de evento por día', default='0')
