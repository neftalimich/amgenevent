# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    specialty_id = fields.Many2one('res.partner.specialty', 'Especialidad')
