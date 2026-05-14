from odoo import models, fields, api

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    equipment_tag = fields.Char(string="Equipment TAG")
    model_name = fields.Char(string="Model")

    location_id = fields.Many2one('stock.location', string="Location")
    building_id = fields.Many2one('building.master', string="Building")
    zone_id = fields.Many2one('zone.master', string="Zone")

    floor = fields.Char(string="Floor")
    room = fields.Char(string="Room")
    ip = fields.Char(string="IP")


    state = fields.Selection([
        ('online', 'Online'),
        ('active', 'Active'),
        ('not active', 'Not Active'),
        ('maintenance', 'Maintenance'),
        ('scrap', 'Scrap'),
    ], default='active')

    asset_code = fields.Char(
        string="Asset Code",
        compute="_compute_asset_code",
        store=True
    )

    digit_count = fields.Integer(
        string="Digit Count",
        compute="_compute_digit_count",
        store=True
    )

    @api.depends('location_id', 'building_id', 'zone_id', 'floor', 'equipment_tag')
    def _compute_asset_code(self):
        for rec in self:
            rec.asset_code = "".join(filter(None, [
                rec.location_id.name if rec.location_id else '',
                rec.building_id.name if rec.building_id else '',
                rec.zone_id.name if rec.zone_id else '',
                str(rec.floor or ''),
                rec.equipment_tag if rec.equipment_tag else '',
            ]))

    @api.depends('asset_code')
    def _compute_digit_count(self):
        for rec in self:
            rec.digit_count = len(rec.asset_code or "")
