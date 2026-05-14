from odoo import models, fields

class BuildingMaster(models.Model):
    _name = 'building.master'
    _description = 'Building Master'

    name = fields.Char(required=True)
