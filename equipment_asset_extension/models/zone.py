from odoo import models, fields

class ZoneMaster(models.Model):
    _name = 'zone.master'
    _description = 'Zone Master'

    name = fields.Char(required=True)
