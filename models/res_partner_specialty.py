# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PartnerSpecialty(models.Model):
    _name = 'res.partner.specialty'
    _description = 'Partner Especialty'

    name = fields.Char(string='Especialidad')
    active = fields.Boolean(string='Activo', default=True)