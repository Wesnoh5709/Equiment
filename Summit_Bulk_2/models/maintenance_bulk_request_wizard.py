from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MaintenanceBulkRequestWizard(models.TransientModel):
    """Wizard: create maintenance requests in bulk for selected equipment.


    """

    _name = 'maintenance.bulk.request.wizard'
    _description = 'Maintenance Bulk Request Wizard'



    # ── Result set ─────────────────────────────────────────────────────────
    equipment_ids = fields.Many2many(
        comodel_name='maintenance.equipment',
        relation='maintenance_bulk_req_equip_rel',
        column1='wizard_id',
        column2='equipment_id',
        string='Matching Equipment',
    )
    equipment_count = fields.Integer(
        string='Equipment Count',
        compute='_compute_equipment_count',
    )

    # ── Bulk request fields ────────────────────────────────────────────────
    request_name = fields.Char(string='Request Name')
    team_id = fields.Many2one(comodel_name='maintenance.team',string='Maintenance Team',)
    request_type = fields.Selection([
        ('annual', 'Annual'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
    ], string='Request Type')
    scheduled_date = fields.Date(string='Scheduled Date')
    priority = fields.Selection(selection=[('0', 'Normal'),('1', 'Important'),('2', 'Very Urgent'),],string='Priority',default='0',required=True,)

    # ──────────────────────────────────────────────────────────────────────
    # Compute
    # ──────────────────────────────────────────────────────────────────────

    @api.model
    def default_get(self, fields_list):
        """Prefill selected equipment from active_ids when opening wizard."""
        vals = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids') or []
        if active_model == 'maintenance.equipment' and active_ids:
            vals['equipment_ids'] = [(6, 0, active_ids)]
        return vals

    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for rec in self:
            rec.equipment_count = len(rec.equipment_ids)


    # ──────────────────────────────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────────────────────────────


    def action_create_requests(self):
        """Create one maintenance.request per selected equipment."""
        self.ensure_one()

        if not self.equipment_ids:
            raise UserError(_(
                'No equipment selected. '
                'Please search and select at least one piece of equipment.'
            ))
        if not self.request_name:
            raise UserError(_('Please provide a Request Name before creating requests.'))

        Request = self.env['maintenance.request']
        created = Request.browse()

        for equipment in self.equipment_ids:
            created |= Request.create({
                'name': self.request_name,
                'equipment_id': equipment.id,
                'maintenance_team_id': (
                    self.team_id.id
                    if self.team_id
                    else equipment.maintenance_team_id.id
                ),
                'schedule_date': self.scheduled_date,
                'priority': self.priority,
                'request_type': self.request_type,
                'company_id': equipment.company_id.id or self.env.company.id,
            })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance Requests'),
            'res_model': 'maintenance.request',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created.ids)],
            'context': {'default_maintenance_type': 'preventive'},
        }
