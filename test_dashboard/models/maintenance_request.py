# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models


class MaintenanceRequest(models.Model):
    """Extends maintenance.request with dashboard data methods.

    All location/tag fields come from equipment_asset_extension on
    maintenance.equipment:
        location_id  (Many2one)
        building_id  (Many2one)
        zone_id      (Many2one)
        floor        (Char)
        room         (Char)
        equipment_tag (Char)
    """
    _inherit = 'maintenance.request'

    # ─── Private helpers ──────────────────────────────────────────────────────

    @api.model
    def _build_domain(self, filters):
        """Convert the JS filter dict into an Odoo domain list."""
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

        # ── Fields from equipment_asset_extension ──────────────────────────
        if filters.get('location_id'):
            domain.append(('equipment_id.location_id', '=', int(filters['location_id'])))
        if filters.get('building_id'):
            domain.append(('equipment_id.building_id', '=', int(filters['building_id'])))
        if filters.get('zone_id'):
            domain.append(('equipment_id.zone_id', '=', int(filters['zone_id'])))
        if filters.get('floor'):
            domain.append(('equipment_id.floor', 'ilike', filters['floor']))
        if filters.get('room'):
            domain.append(('equipment_id.room', 'ilike', filters['room']))
        if filters.get('equipment_tag'):
            domain.append(('equipment_id.equipment_tag', 'ilike', filters['equipment_tag']))
        if filters.get('request_type'):
            domain.append(('request_type', '=', filters['request_type']))
        return domain

    @api.model
    def _m2o_distinct(self, field_name):
        """
        Return [{id, name}] list of distinct Many2one values used on equipment.
        Works for location_id, building_id, zone_id.
        """
        try:
            recs = self.env['maintenance.equipment'].search_read(
                [(field_name, '!=', False)],
                [field_name]
            )
            seen = {}
            for r in recs:
                val = r.get(field_name)
                if val and val[0] not in seen:
                    seen[val[0]] = val[1]
            return [{'id': k, 'name': v}
                    for k, v in sorted(seen.items(), key=lambda x: x[1])]
        except Exception:
            return []

    @api.model
    def _char_distinct(self, field_name):
        """
        Return sorted list of distinct non-empty Char values from equipment.
        Works for floor, room, equipment_tag.
        """
        try:
            table = self.env['maintenance.equipment']._table
            self._cr.execute("""
                SELECT DISTINCT {col} FROM {tbl}
                WHERE {col} IS NOT NULL AND {col} != ''
                ORDER BY {col}
            """.format(col=field_name, tbl=table))
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

        # Tags — maintenance.tag in Odoo 16+
        tags = []
        for model_name in ('maintenance.tag', 'maintenance.equipment.tag'):
            tag_model = self.env.get(model_name)
            if tag_model is not None:
                tags = tag_model.search([]).read(['id', 'name'])
                break

        # Fields from equipment_asset_extension — Many2one dropdowns
        locations = self._m2o_distinct('location_id')
        buildings = self._m2o_distinct('building_id')
        zones     = self._m2o_distinct('zone_id')

        # Plain Char fields
        floors        = self._char_distinct('floor')
        rooms         = self._char_distinct('room')
        equipment_tags = self._char_distinct('equipment_tag')

        # request_type is a fixed Selection — 4 known options
        request_types = [
            {'value': 'annual',      'label': 'Annual (A)'},
            {'value': 'monthly',     'label': 'Monthly (M)'},
            {'value': 'quarterly',   'label': 'Quarterly (Q)'},
            {'value': 'semi_annual', 'label': 'Semi-Annual (S)'},
        ]

        return {
            'teams':          teams,
            'request_types':  request_types,
            'equipment':      equipment,
            'stages':         stages,
            'tags':           tags,
            'locations':      locations,
            'buildings':      buildings,
            'zones':          zones,
            'floors':         floors,
            'rooms':          rooms,
            'equipment_tags': equipment_tags,
        }

    @api.model
    def get_dashboard_data(self, filters):
        """Return the four KPI tile values."""
        domain    = self._build_domain(filters)
        today_str = str(fields.Date.today())
        now_str   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Build equipment domain from filters so the tile reflects current search
        eq_domain = []
        if filters.get('location_id'):
            eq_domain.append(('location_id',   '=', int(filters['location_id'])))
        if filters.get('building_id'):
            eq_domain.append(('building_id',   '=', int(filters['building_id'])))
        if filters.get('zone_id'):
            eq_domain.append(('zone_id',       '=', int(filters['zone_id'])))
        if filters.get('floor'):
            eq_domain.append(('floor',         'ilike', filters['floor']))
        if filters.get('room'):
            eq_domain.append(('room',          'ilike', filters['room']))
        if filters.get('equipment_tag'):
            eq_domain.append(('equipment_tag', 'ilike', filters['equipment_tag']))
        if filters.get('equipment_id'):
            eq_domain.append(('id',            '=', int(filters['equipment_id'])))
        total_equipment = self.env['maintenance.equipment'].search_count(eq_domain)
        total_maintenance = self.search_count(domain)
        maintenance_today = self.search_count(
            domain + [
                ('schedule_date', '>=', today_str + ' 00:00:00'),
                ('schedule_date', '<=', today_str + ' 23:59:59'),
            ])

        # Get IDs of stages marked as done — safe for Odoo 19
        done_stage_ids = self.env['maintenance.stage'].search([('done', '=', True)]).ids
        overdue_domain = domain + [
            ('schedule_date', '!=', False),
            ('schedule_date', '<',  now_str),
        ]
        if done_stage_ids:
            overdue_domain += [('stage_id', 'not in', done_stage_ids)]
        overdue_requests = self.search_count(overdue_domain)

        return {
            'total_equipment':   total_equipment,
            'total_maintenance': total_maintenance,
            'maintenance_today': maintenance_today,
            'maintenance_domain': domain,
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

    # ─── MTTR methods ─────────────────────────────────────────────────────────

    @staticmethod
    def _to_dt(value):
        """
        Normalize datetime.date OR datetime.datetime to datetime.datetime.
        Odoo returns close_date as date and schedule_date as datetime —
        subtracting them directly raises TypeError.
        """
        if not value:
            return None
        if hasattr(value, 'hour'):   # already a datetime
            return value
        from datetime import datetime as _dt
        return _dt(value.year, value.month, value.day, 0, 0, 0)

    @api.model
    def get_mttr_by_team(self, filters, unit='hours'):
        """
        Return [values, labels] — average resolution time per maintenance team.
        Only requests with both schedule_date and close_date are included.
        unit: 'hours' | 'days'
        """
        domain = self._build_domain(filters) + [
            ('schedule_date', '!=', False),
            ('close_date',    '!=', False),
        ]
        recs = self.search_read(domain, ['maintenance_team_id', 'schedule_date', 'close_date'])

        team_totals = {}   # {team_name: [total_seconds, count]}
        for r in recs:
            if not r['maintenance_team_id'] or not r['schedule_date'] or not r['close_date']:
                continue
            team_name = r['maintenance_team_id'][1]
            cd = MaintenanceRequest._to_dt(r['close_date'])
            sd = MaintenanceRequest._to_dt(r['schedule_date'])
            if not cd or not sd:
                continue
            diff = (cd - sd).total_seconds()
            if diff <= 0:
                continue
            if team_name not in team_totals:
                team_totals[team_name] = [0, 0]
            team_totals[team_name][0] += diff
            team_totals[team_name][1] += 1

        divisor = 3600 if unit == 'hours' else 86400
        results = sorted(
            [(name, round(total / count / divisor, 2))
             for name, (total, count) in team_totals.items() if count > 0],
            key=lambda x: x[1], reverse=True
        )
        labels = [r[0] for r in results]
        values = [r[1] for r in results]
        return [values, labels]

    @api.model
    def get_mttr_by_equipment(self, filters, unit='hours'):
        """
        Return [values, labels] — average resolution time per equipment (top 10).
        unit: 'hours' | 'days'
        """
        domain = self._build_domain(filters) + [
            ('equipment_id',  '!=', False),
            ('schedule_date', '!=', False),
            ('close_date',    '!=', False),
        ]
        recs = self.search_read(domain, ['equipment_id', 'schedule_date', 'close_date'])

        eq_totals = {}
        for r in recs:
            if not r['equipment_id'] or not r['schedule_date'] or not r['close_date']:
                continue
            eq_name = r['equipment_id'][1]
            cd = MaintenanceRequest._to_dt(r['close_date'])
            sd = MaintenanceRequest._to_dt(r['schedule_date'])
            if not cd or not sd:
                continue
            diff = (cd - sd).total_seconds()
            if diff <= 0:
                continue
            if eq_name not in eq_totals:
                eq_totals[eq_name] = [0, 0]
            eq_totals[eq_name][0] += diff
            eq_totals[eq_name][1] += 1

        divisor = 3600 if unit == 'hours' else 86400
        results = sorted(
            [(name, round(total / count / divisor, 2))
             for name, (total, count) in eq_totals.items() if count > 0],
            key=lambda x: x[1], reverse=True
        )[:10]
        labels = [r[0] for r in results]
        values = [r[1] for r in results]
        return [values, labels]

    @api.model
    def get_mttr_trend(self, filters, unit='hours'):
        """
        Return [values, labels] — monthly average MTTR for the last 12 months.
        unit: 'hours' | 'days'
        """
        from datetime import timedelta
        import calendar

        today = fields.Date.today()
        # Build list of the last 12 months as (year, month) tuples
        months = []
        y, m = today.year, today.month
        for _ in range(12):
            months.insert(0, (y, m))
            m -= 1
            if m == 0:
                m = 12
                y -= 1

        domain_base = self._build_domain(filters) + [
            ('schedule_date', '!=', False),
            ('close_date',    '!=', False),
        ]

        divisor = 3600 if unit == 'hours' else 86400
        labels = []
        values = []

        for year, month in months:
            last_day = calendar.monthrange(year, month)[1]
            month_start = '%d-%02d-01 00:00:00' % (year, month)
            month_end   = '%d-%02d-%02d 23:59:59' % (year, month, last_day)

            month_domain = domain_base + [
                ('close_date', '>=', month_start),
                ('close_date', '<=', month_end),
            ]
            recs = self.search_read(month_domain, ['schedule_date', 'close_date'])

            diffs = []
            for r in recs:
                if r['schedule_date'] and r['close_date']:
                    cd = MaintenanceRequest._to_dt(r['close_date'])
                    sd = MaintenanceRequest._to_dt(r['schedule_date'])
                    if cd and sd:
                        diff = (cd - sd).total_seconds()
                    else:
                        diff = 0
                    if diff > 0:
                        diffs.append(diff)

            avg = round(sum(diffs) / len(diffs) / divisor, 2) if diffs else 0
            labels.append('%s/%d' % (str(month).zfill(2), year))
            values.append(avg)

        return [values, labels]

    # ─── Maintenance Schedule Matrix ──────────────────────────────────────────

    @api.model
    def get_maintenance_schedule_matrix(self, filters, year=None):
        """
        Return data for the PPM Schedule Excel sheet.
        Matches the layout of the uploaded maintenance_request_report.xlsx template:
          - Columns A-L: equipment info
          - Columns M-BH: 12 months x 4 weeks (type letter in the relevant week cell)
          - Columns BI-BL: TOTAL counts (M / Q / A / S / TOTAL)

        The maintenance type is read from the field `maintenance_type` on
        maintenance.request.  UPDATE THIS FIELD NAME once the real field is added.
        PLACEHOLDER_FIELD = 'maintenance_type'

        Returns a list of row dicts:
          {no, location, building, model, name, tag, room, zone, floor,
           status, asset_code, digit_count,
           schedule: { "month_week": "A"|"M"|"Q"|"S" }}
        """
        import calendar as _cal
        from datetime import date as _date

        if year is None:
            year = _date.today().year

        # ── Fetch all requests with a schedule_date in the target year ─────
        year_domain = self._build_domain(filters) + [
            ('schedule_date', '>=', '%d-01-01 00:00:00' % year),
            ('schedule_date', '<=', '%d-12-31 23:59:59' % year),
            ('equipment_id',  '!=', False),
        ]

        # request_type: Selection field from maintenance_request_type module
        # Values: 'annual'→A  'monthly'→M  'quarterly'→Q  'semi_annual'→S
        maint_type_field = 'request_type'
        TYPE_LETTER_MAP  = {
            'annual':      'A',
            'monthly':     'M',
            'quarterly':   'Q',
            'semi_annual': 'S',
        }

        req_fields = ['equipment_id', 'schedule_date', maint_type_field]
        try:
            recs = self.search_read(year_domain, req_fields)
        except Exception:
            recs = self.search_read(year_domain, ['equipment_id', 'schedule_date'])

        # ── Build per-equipment schedule map ──────────────────────────────
        # equipment_id → { "M_W": type_letter }
        equip_schedule = {}   # {eq_id: {"1_1": "A", "2_1": "M", ...}}
        equip_ids_seen = []   # preserve order

        for r in recs:
            if not r.get('equipment_id') or not r.get('schedule_date'):
                continue

            eq_id   = r['equipment_id'][0]
            sdt     = r['schedule_date']

            # Normalize to datetime
            if hasattr(sdt, 'month'):
                month = sdt.month
                day   = sdt.day
            else:
                continue

            if month < 1 or month > 12 or sdt.year != year:
                continue

            # Week of month: 1=days1-7, 2=8-14, 3=15-21, 4=22+
            week = 1 if day <= 7 else 2 if day <= 14 else 3 if day <= 21 else 4

            # Map Selection key → letter
            type_key    = r.get(maint_type_field) or ''
            type_letter = TYPE_LETTER_MAP.get(type_key, 'M')

            key = '%d_%d' % (month, week)
            if eq_id not in equip_schedule:
                equip_schedule[eq_id] = {}
                equip_ids_seen.append(eq_id)
            # If multiple requests fall in the same week, keep the "heavier" type
            priority = {'A': 4, 'S': 3, 'Q': 2, 'M': 1}
            existing = equip_schedule[eq_id].get(key, '')
            if not existing or priority.get(type_letter, 0) > priority.get(existing, 0):
                equip_schedule[eq_id][key] = type_letter

        if not equip_ids_seen:
            return {'year': year, 'rows': []}

        # ── Fetch equipment details ────────────────────────────────────────
        eq_info = {}
        eq_recs = self.env['maintenance.equipment'].browse(equip_ids_seen).read([
    'id',
    'name',
    'location_id',
    'building_id',
    'zone_id',
    'floor',
    'room',
    'equipment_tag',
    'model_name',
])
        for e in eq_recs:
            eq_info[e['id']] = e

        # ── Build rows ────────────────────────────────────────────────────
        rows = []
        for idx, eq_id in enumerate(equip_ids_seen, start=1):
            e  = eq_info.get(eq_id, {})
            sc = equip_schedule.get(eq_id, {})

            def m2o(field):
                val = e.get(field)
                return val[1] if isinstance(val, (list, tuple)) and len(val) > 1 else (val or '')

            rows.append({
                'no':          idx,
                'location':    m2o('location_id'),
                'building':    m2o('building_id'),
                'model':       e.get('model_name', '') or '',
                'name':        e.get('name', ''),
                'tag':         e.get('equipment_tag', '') or '',
                'room':        e.get('room', '') or '',
                'zone':        m2o('zone_id'),
                'floor':       e.get('floor', '') or '',
                'status':      e.get('state', '') or '',
                'asset_code':  '',    # combine in JS like the template formula
                'schedule':    sc,    # {"1_1": "A", "2_1": "M", ...}
            })

        return {'year': year, 'rows': rows}
