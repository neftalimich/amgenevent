# -*- coding: utf-8 -*-

import datetime
import pytz
import json
import requests

from datetime import datetime, time, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class EventEvent(models.Model):
    _inherit = 'event.event'

    speaker_id = fields.Many2one(
        'res.partner', string='Ponente',
        ondelete='set null'
    )

    moderator_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Moderador(es)'
    )

    limit_exceeded = fields.Boolean(string='Excedió el límite', default=False)

    zoom_id = fields.Char(string='Id Zoom')
    zoom_uuid = fields.Char()
    zoom_host_id = fields.Char()
    zoom_join_url = fields.Char()

    zoom_pass = fields.Char(string='Password Zoom')
    zoom_link = fields.Char(string='Enlace Zoom')

    minutes_before = fields.Integer(string='Minutos Antes', default=20)
    minutes_after = fields.Integer(string='Minutos Después', default=30)

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

        # matches = self.env["event.event"].search([
        #     ('id', '!=', event_id),
        #     '&',
        #     '|',
        #     '&', ('date_begin', '<=', event_date_begin), ('date_end', '>=', event_date_begin),
        #     '&', ('date_begin', '<=', event_date_end), ('date_end', '>=', event_date_end),
        #     '|', ('stage_id', '=', 2), ('stage_id', '=', 3)
        # ])
        # if len(matches) > 0:
        #     raise UserError('El horario ya está reservador por el evento: {}.'.format(matches[0].name))

        event_limit = 4

        events = self.env["event.event"].search([
            ('id', '!=', event_id),
            ('date_begin', '>=', event_date_begin.date()), ('date_begin', '<=', event_date_end.date()),
            '|',
            ('stage_id', '=', 2),
            '|',
            ('stage_id', '=', 3),
            ('stage_id', '=', 4)
        ])

        print('Num Events:', len(events))

        if len(events) >= event_limit:
            self.limit_exceeded = True
        else:
            self.limit_exceeded = False

        return True

    def cancel_event_exceed(self):
        event_id = self.id
        event_date_begin = self.date_begin
        event_date_end = self.date_end

        events = self.env["event.event"].search([
            ('id', '!=', event_id),
            ('date_begin', '>=', event_date_begin.date()), ('date_begin', '<=', event_date_begin.date()),
            '|',
            ('stage_id', '=', 2),
            '|',
            ('stage_id', '=', 3),
            ('stage_id', '=', 4)
        ], order='id ASC')

        event_limit = 4

        events[0:event_limit].write({'limit_exceeded': False})
        events[event_limit:].write({'limit_exceeded': True})

        return True

    # Write
    def write(self, vals):
        if 'stage_id' in vals:
            current_stage_id = self.stage_id.id
            new_stage_id = vals['stage_id']

            if current_stage_id == 1 or current_stage_id == 5:
                if new_stage_id != 2:
                    raise UserError('Primero debes Reservar el evento')

            if new_stage_id == 1:
                self.limit_exceeded = False
            elif new_stage_id == 2:
                self.validate_event_date(self.date_begin, self.date_end)
            elif new_stage_id == 3:
                if not self.zoom_link:
                    print('Create Zoom meeting')
                    # self.create_zoom_meeting()
            elif new_stage_id == 4:
                print('Event Ended')
            elif new_stage_id == 5:
                print('Cancel Event')
                self.limit_exceeded = False
                self.cancel_event_exceed()
                if self.zoom_link:
                    print('Cancel Meeting')
                    # self.cancel_zoom_meeting()

            print('Stage Modified from {} to {}'.format(current_stage_id, new_stage_id))

        return super(EventEvent, self).write(vals)

    # ZOOM API
    def create_zoom_meeting(self):
        print('Create Zoom Meeting', self.id)
        date_begin = self.date_begin - timedelta(minutes=self.minutes_before)
        date_end = self.date_begin + timedelta(minutes=self.minutes_after)
        duration = int((date_end - date_begin).total_seconds() / 60)

        kwargs = {
            "topic": self.name,
            "type": 2,
            "password": self.zoom_pass or "",
            "start_time": self._datetime_localize(date_begin),
            "duration": duration,
            "timezone": self.env.user.tz,
            "agenda": ""
        }

        print('Meeting', kwargs)
        url = "https://api.zoom.us/v2/users/me/meetings"
        req_headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOm51bGwsImlzcyI6IkxrMW9RY2loU0RPcF93NVVHZkpUcUEiLCJleHAiOjE2MTI5OTE2MjMsImlhdCI6MTYxMjM4NjgyNH0.KjYWp0wWCzzXe4ANTyXJW2WQ30fG0_pCUdU9A3CrhiM'
            }
        req = requests.post(
            url,
            headers=req_headers,
            data=json.dumps(kwargs)
        )

        result = req.json()
        print("result", result)
        self.zoom_uuid = result['uuid']
        self.zoom_id = result['id']
        self.zoom_host_id = result['host_id']
        self.zoom_join_url = result['join_url']
        self.zoom_link = result['join_url']
        print(self.zoom_link)
        return True

    def update_zoom_meeting(self, date_begin, date_end):
        print('Update Zoom Meeting', self.id)
        return 'zoom.com/XYZ'

    def cancel_zoom_meeting(self, date_begin, date_end):
        print('Cancel Zoom Meeting', self.id)
        return 'zoom.com/XYZ'

    # EMAIL
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

    # UTILITIES
    def _datetime_localize(self, date):
        """
        Convert utc time to local timezone.
        """
        user_tz = self.env.user.tz
        if user_tz:
            local = pytz.timezone(user_tz)
            is_var_str = isinstance(date, str)
            if not is_var_str:
                date = date.strftime("%Y-%m-%d %H:%M:%S")
            display_date_result = datetime.strftime(
                pytz.utc.localize(datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),
                "%Y-%m-%d %H:%M:%S"
            )
            return display_date_result
        else:
            raise UserError("Please set user timezone")
