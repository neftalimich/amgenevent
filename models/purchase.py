# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    event_ids = fields.One2many(
        'event.event',
        'order_id',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},
        domain="[('stage_id', '=', 4), ('speaker_id', '=', partner_id)]"
    )
