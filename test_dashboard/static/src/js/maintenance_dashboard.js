/** @odoo-module **/

import { registry }   from "@web/core/registry";
import { Component }  from "@odoo/owl";
import { onWillStart, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// ─── Colour palette shared by both charts ────────────────────────────────────
const COLORS = [
    "#4361ee", "#3a0ca3", "#7209b7", "#f72585", "#4cc9f0",
    "#06d6a0", "#fb8500", "#e63946", "#118ab2", "#ffd166",
];

export class MaintenanceDashboard extends Component {
    static template = "test_dashboard.MaintenanceDashboard";

    setup() {
        this.orm    = useService("orm");
        this.action = useService("action");

        this.stageChartRef     = useRef("requests_by_stage");
        this.equipmentChartRef = useRef("requests_by_equipment");

        this.state = useState({
            // dropdown option lists
            opt_teams:     [],
            opt_equipment: [],
            opt_stages:    [],
            opt_tags:      [],
            opt_locations: [],
            opt_zones:     [],
            opt_buildings: [],
            opt_floors:    [],
            opt_rooms:     [],

            // active filter values
            f_team_id:      "",
            f_equipment_id: "",
            f_date_from:    "",
            f_date_to:      "",
            f_stage_id:     "",
            f_location:     "",
            f_zone:         "",
            f_building:     "",
            f_floor:        "",
            f_room:         "",
            f_tag_id:       "",

            // KPI values
            total_equipment:   0,
            total_maintenance: 0,
            maintenance_today: 0,
            overdue_requests:  0,

            // internal chart handles
            _charts: [],

            loading: true,
        });

        onWillStart(async () => {
            await this._loadFilterOptions();
            await this._loadDashboardData();
        });
    }

    // ─── Filter helpers ───────────────────────────────────────────────────────

    async _loadFilterOptions() {
        const opts = await this.orm.call(
            "maintenance.request", "get_filter_options", []);
        this.state.opt_teams     = opts.teams     || [];
        this.state.opt_equipment = opts.equipment || [];
        this.state.opt_stages    = opts.stages    || [];
        this.state.opt_tags      = opts.tags      || [];
        this.state.opt_locations = opts.locations || [];
        this.state.opt_zones     = opts.zones     || [];
        this.state.opt_buildings = opts.buildings || [];
        this.state.opt_floors    = opts.floors    || [];
        this.state.opt_rooms     = opts.rooms     || [];
    }

    _buildFilters() {
        const f = {};
        if (this.state.f_team_id)      f.team_id      = this.state.f_team_id;
        if (this.state.f_equipment_id) f.equipment_id = this.state.f_equipment_id;
        if (this.state.f_date_from)    f.date_from    = this.state.f_date_from;
        if (this.state.f_date_to)      f.date_to      = this.state.f_date_to;
        if (this.state.f_stage_id)     f.stage_id     = this.state.f_stage_id;
        if (this.state.f_location)     f.location_id  = this.state.f_location;
        if (this.state.f_zone)         f.zone         = this.state.f_zone;
        if (this.state.f_building)     f.building     = this.state.f_building;
        if (this.state.f_floor)        f.floor        = this.state.f_floor;
        if (this.state.f_room)         f.room         = this.state.f_room;
        if (this.state.f_tag_id)       f.tag_ids      = [parseInt(this.state.f_tag_id)];
        return f;
    }

    // ─── Data loading ─────────────────────────────────────────────────────────

    async _loadDashboardData() {
        this.state.loading = true;
        this.state._charts.forEach(c => c.destroy());
        this.state._charts = [];

        const filters = this._buildFilters();

        const kpi = await this.orm.call(
            "maintenance.request", "get_dashboard_data", [filters]);
        this.state.total_equipment   = kpi.total_equipment;
        this.state.total_maintenance = kpi.total_maintenance;
        this.state.maintenance_today = kpi.maintenance_today;
        this.state.overdue_requests  = kpi.overdue_requests;

        this.state.loading = false;

        setTimeout(() => this._renderCharts(filters), 80);
    }

    async _renderCharts(filters) {
        await this._renderStageChart(filters);
        await this._renderEquipmentChart(filters);
    }

    async _renderStageChart(filters) {
        const canvas = this.stageChartRef.el;
        if (!canvas) return;
        const [counts, labels] = await this.orm.call(
            "maintenance.request", "get_requests_by_stage", [filters]);
        const chart = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Requests",
                    data: counts,
                    backgroundColor: COLORS.slice(0, labels.length),
                    borderRadius: 6,
                    borderSkipped: false,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: {
                        label: ctx => ` ${ctx.parsed.y} request(s)`
                    }},
                },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0, color: "#6c757d" }, grid: { color: "rgba(0,0,0,.05)" } },
                    x: { ticks: { color: "#6c757d" }, grid: { display: false } },
                },
            },
        });
        this.state._charts.push(chart);
    }

    async _renderEquipmentChart(filters) {
        const canvas = this.equipmentChartRef.el;
        if (!canvas) return;
        const [counts, labels] = await this.orm.call(
            "maintenance.request", "get_requests_by_equipment", [filters]);
        const chart = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Requests",
                    data: counts,
                    backgroundColor: COLORS.slice(0, labels.length),
                    borderRadius: 6,
                    borderSkipped: false,
                }],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: {
                        label: ctx => ` ${ctx.parsed.x} request(s)`
                    }},
                },
                scales: {
                    x: { beginAtZero: true, ticks: { precision: 0, color: "#6c757d" }, grid: { color: "rgba(0,0,0,.05)" } },
                    y: { ticks: { color: "#6c757d" }, grid: { display: false } },
                },
            },
        });
        this.state._charts.push(chart);
    }

    // ─── Event handlers ───────────────────────────────────────────────────────

    async onSearch() {
        await this._loadDashboardData();
    }

    async onReset() {
        Object.assign(this.state, {
            f_team_id: "", f_equipment_id: "", f_date_from: "",
            f_date_to: "", f_stage_id: "", f_location: "",
            f_zone: "", f_building: "", f_floor: "",
            f_room: "", f_tag_id: "",
        });
        await this._loadDashboardData();
    }

    // ─── Tile click actions ───────────────────────────────────────────────────

    onClickEquipment() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "All Equipment",
            res_model: "maintenance.equipment",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    onClickMaintenance() {
        const f = this._buildFilters();
        const domain = [];
        if (f.team_id)      domain.push(["maintenance_team_id", "=", parseInt(f.team_id)]);
        if (f.equipment_id) domain.push(["equipment_id", "=", parseInt(f.equipment_id)]);
        if (f.date_from)    domain.push(["request_date", ">=", f.date_from]);
        if (f.date_to)      domain.push(["request_date", "<=", f.date_to]);
        if (f.stage_id)     domain.push(["stage_id", "=", parseInt(f.stage_id)]);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Maintenance Requests",
            res_model: "maintenance.request",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain,
        });
    }

    onClickToday() {
        const today = new Date().toISOString().slice(0, 10);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Maintenance Today",
            res_model: "maintenance.request",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: [["request_date", "=", today]],
        });
    }

    onClickOverdue() {
        const now = new Date().toISOString().replace("T", " ").slice(0, 19);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Overdue Requests",
            res_model: "maintenance.request",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: [
                ["schedule_date", "<", now],
                ["close_date",    "=", false],
            ],
        });
    }
}

registry.category("actions").add("test_dashboard", MaintenanceDashboard);
