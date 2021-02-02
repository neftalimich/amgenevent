# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    specialty = fields.Char(string='Especialidad')

    pre_state = fields.Selection([
        ('draft', 'Pendiente'),
        ('confirmed', 'Asistirá'),
        ('canceled', 'No Aistirá'),
        ('likely', 'Posiblemente'),
        ('unanswered', 'No Contestó'),
    ], string='Respuesta', default='draft', tracking=True)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for registration in self:
            if registration.partner_id:
                if registration.partner_id.specialty_id:
                    self.specialty = registration.partner_id.specialty_id.name
