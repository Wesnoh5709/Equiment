# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models


class MaintenanceRequest(models.Model):
    """Extends maintenance.request with dashboard data methods."""
    _inherit = 'maintenance.request'

    # ─── Additional location fields ───────────────────────────────────────────
    zone     = fields.Char(string='Zone')
    building = fields.Char(string='Building')
    floor    = fields.Char(string='Floor')
    room     = fields.Char(string='Room')

    # ─── Private helpers ──────────────────────────────────────────────────────

    @api.model
    def _build_domain(self, filters):
        domain = []
        if filters.get('team_id'):
            domain.append(('maintenance_team_id', '=', int(filters['team_id'])))
        if filters.get('equipment_id'):
            domain.append(('equipment_id', '=', int(filters['equipment_id'])))
        if filters.get('date_from'):
            domain.append(('request_date', '>=', filters['date_from']))
        if filters.get('date_to'):
            domain.append(('request_date', '<=', filters['date_to']))
        if filters.get('stage_id'):
            domain.append(('stage_id', '=', int(filters['stage_id'])))
        if filters.get('location_id'):
            domain.append(('equipment_id.location_id', '=', int(filters['location_id'])))
        if filters.get('zone'):
            domain.append(('zone', 'ilike', filters['zone']))
        if filters.get('building'):
            domain.append(('building', 'ilike', filters['building']))
        if filters.get('floor'):
            domain.append(('floor', 'ilike', filters['floor']))
        if filters.get('room'):
            domain.append(('room', 'ilike', filters['room']))
        if filters.get('tag_ids'):
            domain.append(('tag_ids', 'in', filters['tag_ids']))
        return domain

    @api.model
    def _safe_distinct_char(self, table, column):
        """Return sorted distinct non-empty Char values from a table column."""
        try:
            self._cr.execute("""
                SELECT DISTINCT %(col)s
                FROM %(tbl)s
                WHERE %(col)s IS NOT NULL
                  AND %(col)s != ''
                ORDER BY %(col)s
            """ % {'col': column, 'tbl': table})
            return [r[0] for r in self._cr.fetchall()]
        except Exception:
            self._cr.rollback()
            return []

    # ─── Public API methods called from JS ────────────────────────────────────

    @api.model
    def get_filter_options(self):
        """Return all dropdown option lists for the search panel."""

        teams = self.env['maintenance.team'].search([]).read(['id', 'name'])

        equipment = self.env['maintenance.equipment'].search(
            [], order='name').read(['id', 'name'])

        stages = self.env['maintenance.stage'].search(
            [], order='sequence').read(['id', 'name'])

        # Tags — model name differs between versions, guard both
        tags = []
        for model_name in ('maintenance.tag', 'maintenance.equipment.tag'):
            tag_model = self.env.get(model_name)
            if tag_model is not None:
                tags = tag_model.search([]).read(['id', 'name'])
                break

        # Locations — Many2one on equipment in Odoo 17+
        # Use ORM so we get id+name pairs for the dropdown
        locations = []
        eq_fields = self.env['maintenance.equipment'].fields_get(
            attributes=['type'])
        if 'location_id' in eq_fields:
            # location_id is a Many2one → read distinct records via ORM
            loc_data = self.env['maintenance.equipment'].search_read(
                [('location_id', '!=', False)],
                ['location_id'])
            seen = {}
            for rec in loc_data:
                lid, lname = rec['location_id']
                if lid not in seen:
                    seen[lid] = lname
            locations = [{'id': k, 'name': v}
                         for k, v in sorted(seen.items(), key=lambda x: x[1])]
        elif 'location' in eq_fields:
            # Older: plain Char field
            locations = self._safe_distinct_char(
                'maintenance_equipment', 'location')
            locations = [{'id': v, 'name': v} for v in locations]

        return {
            'teams':     teams,
            'equipment': equipment,
            'stages':    stages,
            'tags':      tags,
            'locations': locations,
            'zones':     self._safe_distinct_char('maintenance_request', 'zone'),
            'buildings': self._safe_distinct_char('maintenance_request', 'building'),
            'floors':    self._safe_distinct_char('maintenance_request', 'floor'),
            'rooms':     self._safe_distinct_char('maintenance_request', 'room'),
        }

    @api.model
    def get_dashboard_data(self, filters):
        """Return the four KPI tile values."""
        domain    = self._build_domain(filters)
        today_str = str(fields.Date.today())
        now_str   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        total_equipment   = self.env['maintenance.equipment'].search_count([])
        total_maintenance = self.search_count(domain)
        maintenance_today = self.search_count(
            domain + [('request_date', '=', today_str)])

        overdue_domain = domain + [
            ('schedule_date', '!=', False),
            ('schedule_date', '<',  now_str),
            ('close_date',    '=',  False),
        ]
        # Exclude done stages if the field exists
        Stage = self.env['maintenance.stage']
        if 'done' in Stage.fields_get(attributes=['type']):
            done_ids = Stage.search([('done', '=', True)]).ids
            if done_ids:
                overdue_domain += [('stage_id', 'not in', done_ids)]

        overdue_requests = self.search_count(overdue_domain)

        return {
            'total_equipment':   total_equipment,
            'total_maintenance': total_maintenance,
            'maintenance_today': maintenance_today,
            'overdue_requests':  overdue_requests,
        }

    @api.model
    def get_requests_by_stage(self, filters):
        """Return [counts, labels] for the stage bar chart."""
        domain = self._build_domain(filters)
        groups = self.read_group(domain, ['stage_id'], ['stage_id'])
        labels, counts = [], []
        for g in groups:
            if g.get('stage_id'):
                labels.append(g['stage_id'][1])
                counts.append(g['stage_id_count'])
        return [counts, labels]

    @api.model
    def get_requests_by_equipment(self, filters):
        """Return [counts, labels] for the equipment horizontal bar chart (top 10)."""
        domain = self._build_domain(filters) + [('equipment_id', '!=', False)]
        groups = self.read_group(domain, ['equipment_id'], ['equipment_id'])
        groups_sorted = sorted(
            [g for g in groups if g.get('equipment_id')],
            key=lambda g: g['equipment_id_count'],
            reverse=True
        )[:10]
        labels = [g['equipment_id'][1] for g in groups_sorted]
        counts = [g['equipment_id_count'] for g in groups_sorted]
        return [counts, labels]
