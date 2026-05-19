from odoo import models, fields


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    request_type = fields.Selection([
        ('annual', 'Annual'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
    ], string='Request Type')
