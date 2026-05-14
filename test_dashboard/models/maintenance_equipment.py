# -*- coding: utf-8 -*-
from odoo import fields, models


class MaintenanceEquipment(models.Model):
    """Extends maintenance.equipment with detailed location fields."""
    _inherit = 'maintenance.equipment'

    zone = fields.Char(string='Zone', help='Zone where the equipment is located')
    building = fields.Char(string='Building', help='Building where the equipment is located')
    floor = fields.Char(string='Floor', help='Floor where the equipment is located')
    room = fields.Char(string='Room', help='Room where the equipment is located')
