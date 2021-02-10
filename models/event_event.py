# -*- coding: utf-8 -*-

import datetime
import pytz
import json
import requests

from datetime import datetime, time, timedelta
from pytz import timezone

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


def _datetime_timezone(date, date_tz):
    return datetime.strftime(date.astimezone(timezone(date_tz)), "%Y-%m-%d %H:%M:%S")


class EventEvent(models.Model):
    _inherit = 'event.event'
    token = 'Bearer'

    description = fields.Html(default='')

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

    zoom_topic = fields.Char(string='Tema Zoom')
    zoom_pass = fields.Char(string='Password Zoom')
    zoom_link = fields.Char(string='Enlace Zoom')

    minutes_before = fields.Integer(string='Minutos Antes', default=20)
    minutes_after = fields.Integer(string='Minutos Después', default=30)
    duration = fields.Integer(string='Duración(min)', default=0, help='Duración en minutos.')

    order_id = fields.Many2one(comodel_name='purchase.order', string='Compra')

    # On Change
    @api.onchange('duration')
    def _onchange_duration(self):
        if self.date_begin:
            self.date_end = self.date_begin + timedelta(minutes=self.duration)

    @api.onchange('date_end')
    def _onchange_date_end(self):
        if self.date_begin:
            self.duration = int((self.date_end - self.date_begin).total_seconds() / 60)

    # Validation
    def validate_event_date(self, new_date_begin, new_date_end):
        event_id = self.id
        event_date_begin = new_date_begin if new_date_begin is not None else self.date_begin
        event_date_end = new_date_end if new_date_end is not None else self.date_end

        if not event_date_begin or not event_date_end:
            return False

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

        print('Event - Num Events this day:', len(events))

        if len(events) >= event_limit:
            return True
        else:
            return False

    def cancel_event_exceed(self, date):
        event_id = self.id
        event_date = date if date is not None else self.date_begin

        if not event_date:
            return False

        if event_date:
            events = self.env["event.event"].search([
                ('id', '!=', event_id),
                ('date_begin', '>=', event_date.date()), ('date_begin', '<=', event_date.date()),
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

    # Create
    @api.model
    def create(self, vals):
        print("Event - Create", json.dumps(vals))

        date_tz = vals['date_tz'] if 'date_tz' in vals else self.env.user.tz
        date_begin = datetime.strptime(vals['date_begin'], "%Y-%m-%d %H:%M:%S")
        date_end = datetime.strptime(vals['date_end'], "%Y-%m-%d %H:%M:%S")
        minutes_before = vals['minutes_before'] if 'minutes_before' in vals else 0
        minutes_after = vals['minutes_after'] if 'minutes_before' in vals else 0

        zoom_date_begin = date_begin - timedelta(minutes=minutes_before)
        zoom_date_end = date_end + timedelta(minutes=minutes_after)
        zoom_duration = int((zoom_date_end - zoom_date_begin).total_seconds() / 60)

        vals['limit_exceeded'] = self.validate_event_date(date_begin, date_end)

        if not vals['limit_exceeded']:
            vals['stage_id'] = 2
            kwargs = {
                "topic": vals['zoom_topic'] or vals['name'] or "",
                "type": 2,
                "password": vals['zoom_pass'] or "",
                "start_time": _datetime_timezone(zoom_date_begin, date_tz),
                "duration": zoom_duration,
                "timezone": date_tz
            }
            print(kwargs)
            result = self.create_zoom_meeting(kwargs)
            if result:
                vals['zoom_uuid'] = result['uuid']
                vals['zoom_id'] = result['id']
                vals['zoom_host_id'] = result['host_id']
                vals['zoom_join_url'] = result['join_url']
                vals['zoom_link'] = result['join_url']
                vals['stage_id'] = 3
        else:
            print("Send Email to User")

        return super(EventEvent, self).create(vals)

    # Write
    def write(self, vals):
        print('Write', self.id, json.dumps(vals))

        if 'limit_exceeded' in vals:
            return super(EventEvent, self).write(vals)

        date_tz = vals['date_tz'] if 'date_tz' in vals else self.env.user.tz
        date_begin = \
            datetime.strptime(vals['date_begin'], "%Y-%m-%d %H:%M:%S") if 'date_begin' in vals else self.date_begin
        date_end = \
            datetime.strptime(vals['date_end'], "%Y-%m-%d %H:%M:%S") if 'date_end' in vals else self.date_end
        minutes_before = vals['minutes_before'] if 'minutes_before' in vals else self.minutes_before
        minutes_after = vals['minutes_after'] if 'minutes_before' in vals else self.minutes_after

        zoom_topic = vals['zoom_topic'] if 'zoom_topic' in vals else (self.zoom_topic if self.zoom_topic else self.name)
        zoom_pass = vals['zoom_pass'] if 'zoom_pass' in vals else self.zoom_pass
        zoom_date_begin = date_begin - timedelta(minutes=minutes_before)
        zoom_date_end = date_end + timedelta(minutes=minutes_after)
        zoom_duration = int((zoom_date_end - zoom_date_begin).total_seconds() / 60)

        kwargs = {
            "topic": zoom_topic or "",
            "type": 2,
            "password": zoom_pass or "",
            "start_time": _datetime_timezone(zoom_date_begin, date_tz),
            "duration": zoom_duration,
            "timezone": date_tz
        }

        if 'stage_id' in vals:
            current_stage_id = self.stage_id.id
            new_stage_id = vals['stage_id']

            if current_stage_id == 1 or current_stage_id == 5:
                if new_stage_id != 2:
                    raise UserError('Primero debes Reservar el evento.')

            if new_stage_id == 1:
                vals['limit_exceeded'] = False
            elif new_stage_id == 2:
                vals['limit_exceeded'] = self.validate_event_date(date_begin, date_end)
            elif new_stage_id == 3:
                if not self.zoom_id:
                    result = self.create_zoom_meeting(kwargs)
                    if result:
                        vals['zoom_uuid'] = result['uuid']
                        vals['zoom_id'] = result['id']
                        vals['zoom_host_id'] = result['host_id']
                        vals['zoom_join_url'] = result['join_url']
                        vals['zoom_link'] = result['join_url']
            elif new_stage_id == 4:
                print('Event Ended')
            elif new_stage_id == 5:
                print('Cancel Event')
                vals['limit_exceeded'] = False
                self.cancel_event_exceed(date_begin)
                if self.zoom_id:
                    result = self.cancel_zoom_meeting(self.zoom_id)
                    if result:
                        vals['zoom_uuid'] = None
                        vals['zoom_id'] = None
                        vals['zoom_host_id'] = None
                        vals['zoom_join_url'] = None
                        vals['zoom_link'] = None
        else:
            if ('date_begin' in vals or 'date_end') in vals:
                self.cancel_event_exceed(date_begin)
                self.validate_event_date(date_begin, date_end)
            if 'name' in vals or 'zoom_topic' in vals or 'zoom_pass' in vals \
                    or 'date_begin' in vals or 'date_end' in vals \
                    or 'minutes_before' in vals or 'minutes_after' in vals:
                if self.zoom_id:
                    self.update_zoom_meeting(kwargs)

        return super(EventEvent, self).write(vals)

    # ZOOM API
    def create_zoom_meeting(self, kwargs):
        print("Create Zoom Meeting", self.id, kwargs)

        # Test
        # return {'id': 1234, 'uuid': 'UUID Test', 'host_id': 'Host Id Test', 'join_url': 'URL Test'}

        # Zoom Patch Request
        url = "https://api.zoom.us/v2/users/me/meetings"
        req_headers = {
            'Content-Type': 'application/json',
            'Authorization': self.token
        }

        try:
            req = requests.post(
                url,
                headers=req_headers,
                data=json.dumps(kwargs)
            )
            print('Zoom Request - Status Code', req.status_code)
            if req.status_code != 201:
                print("Error - Zoom - Create Meeting")
                print(req)
                return False
            else:
                result = req.json()
                print("Success - Zoom - Creating Meeting", result)
                return result
        except requests.exceptions.RequestException as e:
            print("Error - Zoom - Request - Create Meeting")
            print(e)
            return False

    def update_zoom_meeting(self, kwargs):
        print('Update Zoom Meeting', self.id, kwargs)

        # Zoom patch request
        url = "https://api.zoom.us/v2/meetings" + self.zoom_id
        req_headers = {
            'Content-Type': 'application/json',
            'Authorization': self.token
        }
        try:
            req = requests.patch(url, headers=req_headers, data=json.dumps(kwargs))
            print(req.status_code)
            if req.status_code != 200:
                print("Error - Zoom - Update Meeting")
                print(req)
            else:
                print("Success - Zoom - Update Meeting")
                print(req)
        except requests.exceptions.RequestException as e:
            print("Error - Zoom - Request - Update Meeting")
            print(e)

        return True

    def cancel_zoom_meeting(self, zoom_id):
        print('Cancel Zoom Meeting', self.id, zoom_id)
        # Zoom delete request
        url = "https://api.zoom.us/v2/meetings/" + zoom_id
        req_headers = {
            'Authorization': self.token
        }

        try:
            req = requests.delete(url, headers=req_headers)
            if req.status_code != 204:
                print("Error - Zoom - Cancel Meeting")
                return False
            else:
                print("Success - Zoom - Cancel Meeting", self.id, zoom_id)
                return True
        except requests.exceptions.RequestException as e:
            print("Error - Zoom - Request - Cancel Meeting")
            print(e)
            return False

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
