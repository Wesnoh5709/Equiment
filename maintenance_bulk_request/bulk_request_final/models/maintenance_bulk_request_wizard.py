from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MaintenanceBulkRequestWizard(models.TransientModel):
    """Wizard: create maintenance requests for equipment selected in the list view.

    Selected equipment is received via active_ids in the context.
    No filter fields needed — filtering happens in the list view itself.
    """

    _name = 'maintenance.bulk.request.wizard'
    _description = 'Maintenance Bulk Request Wizard'

    # Pre-loaded from active_ids when the wizard is opened
    equipment_ids = fields.Many2many(
        comodel_name='maintenance.equipment',
        relation='maintenance_bulk_req_equip_rel',
        column1='wizard_id',
        column2='equipment_id',
        string='Selected Equipment',
        readonly=True,
    )
    equipment_count = fields.Integer(
        string='Equipment Count',
        compute='_compute_equipment_count',
    )

    # ── Bulk request fields ────────────────────────────────────────────────
    request_name = fields.Char(string='Request Name', required=True)
    team_id = fields.Many2one(
        comodel_name='maintenance.team',
        string='Maintenance Team',
    )
    scheduled_date = fields.Date(string='Scheduled Date')
    priority = fields.Selection(
        selection=[
            ('0', 'Normal'),
            ('1', 'Important'),
            ('2', 'Very Urgent'),
        ],
        string='Priority',
        default='0',
        required=True,
    )

    # ──────────────────────────────────────────────────────────────────────
    # Default / compute
    # ──────────────────────────────────────────────────────────────────────

    @api.model
    def default_get(self, fields_list):
        """Pre-populate equipment_ids from the equipment selected in the list view."""
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            res['equipment_ids'] = [fields.Command.set(active_ids)]
        return res

    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for rec in self:
            rec.equipment_count = len(rec.equipment_ids)

    # ──────────────────────────────────────────────────────────────────────
    # Action
    # ──────────────────────────────────────────────────────────────────────

    def action_create_requests(self):
        """Create one maintenance.request per selected equipment."""
        self.ensure_one()

        if not self.equipment_ids:
            raise UserError(_(
                'No equipment found. Please select at least one piece of '
                'equipment from the list before opening this wizard.'
            ))

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
                'maintenance_type': 'preventive',
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
