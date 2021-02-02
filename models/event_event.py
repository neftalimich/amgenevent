# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EventEvent(models.Model):
    _inherit = 'event.event'

    speaker_id = fields.Many2one(
        'res.partner', string='Ponente',
        ondelete='set null', domain="[('category_id.name', '=', 'Ponente')]")

    moderator_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Moderador(es)',
        domain="[('category_id.name', '=', 'Moderador')]"
    )

    zoom_link = fields.Char(string='Enlace Zoom')
    zoom_pass = fields.Char(string='Password Zoom')

    order_id = fields.Many2one(comodel_name='purchase.order', string='Compra')

    # Validation
    def validate_event_date(self, new_date_begin, new_date_end):
        event_id = self.id
        event_date_begin = self.date_begin
        event_date_end = self.date_end

        if new_date_begin is not None:
            event_date_begin = new_date_begin
        if new_date_end is not None:
            event_date_end = new_date_end

        matches = self.env["event.event"].search([
            ('id', '!=', event_id),
            '&',
            '|',
            '&', ('date_begin', '<=', event_date_begin), ('date_end', '>=', event_date_begin),
            '&', ('date_begin', '<=', event_date_end), ('date_end', '>=', event_date_end),
            '|', ('stage_id', '=', 2), ('stage_id', '=', 3)
        ])
        if len(matches) > 0:
            raise UserError('El horario ya está reservador por el evento: {}.'.format(matches[0].name))

        return True

    def write(self, vals):
        if 'stage_id' in vals:
            current_stage_id = self.stage_id.id
            new_stage_id = vals['stage_id']
            if current_stage_id == 1:
                if new_stage_id != 2:
                    raise UserError('Primero debes Reservar el evento')
                self.validate_event_date(self.date_begin, self.date_end)
            if current_stage_id == 2:
                if new_stage_id == 3:
                    self.create_zoom_meeting()
            print('Stage Modified from {} to {}'.format(current_stage_id, new_stage_id))

        if 'date_begin' in vals or 'date_end' in vals:
            event_date_begin = self.date_begin
            event_date_end = self.date_end
            event_zoom_link = self.zoom_link
            if 'date_begin' in vals:
                event_date_begin = vals['date_begin']
            if 'date_end' in vals:
                event_date_end = vals['date_end']
            if current_stage_id == 3:
                self.validate_event_date(event_date_begin, event_date_end)
                # self.change_date_zoom_conference(event_zoom_link, event_date_begin, event_date_end)

        return super(EventEvent, self).write(vals)

    def action_send_event_mail(self):
        self.ensure_one()
        template = self.env.ref('amgenevent.event_mail_template_invitation')
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        ctx = dict(
            default_model='event.event',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            custom_layout="mail.mail_notification_light",
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    # ZOOM API
    def create_zoom_meeting(self):
        print('Create Zoom Meeting', self.id)
        return ''
