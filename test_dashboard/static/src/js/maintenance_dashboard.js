/** @odoo-module **/

import { registry }   from "@web/core/registry";
import { Component }  from "@odoo/owl";
import { onWillStart, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

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
        this.dashboardRef      = useRef("dashboard_root");

        this.state = useState({
            opt_teams: [], opt_equipment: [], opt_stages: [], opt_tags: [],
            opt_request_types: [],
            opt_locations: [], opt_buildings: [], opt_zones: [],
            opt_floors: [], opt_rooms: [], opt_equipment_tags: [],

            f_team_id: "", f_equipment_id: "", f_date_from: "", f_date_to: "",
            f_request_type: "",
            f_stage_id: "", f_location_id: "", f_building_id: "", f_zone_id: "",
            f_floor: "", f_room: "", f_equipment_tag: "", f_request_type: "",


            total_equipment: 0, total_maintenance: 0,
            maintenance_today: 0, overdue_requests: 0,

            // Cached chart data for Excel export
            _chartData: {},
            _charts: [],
            loading: true,
            exporting_excel: false,
            exporting_pdf: false,
        });

        onWillStart(async () => {
            await this._loadFilterOptions();
            await this._loadDashboardData();
        });
    }

    // ─── Filter helpers ───────────────────────────────────────────────────────

    async _loadFilterOptions() {
        const opts = await this.orm.call("maintenance.request", "get_filter_options", []);
        this.state.opt_teams          = opts.teams          || [];
        this.state.opt_equipment      = opts.equipment      || [];
        this.state.opt_stages         = opts.stages         || [];
        this.state.opt_tags           = opts.tags           || [];
        this.state.opt_locations      = opts.locations      || [];
        this.state.opt_buildings      = opts.buildings      || [];
        this.state.opt_zones          = opts.zones          || [];
        this.state.opt_floors         = opts.floors         || [];
        this.state.opt_rooms          = opts.rooms          || [];
        this.state.opt_equipment_tags  = opts.equipment_tags  || [];
        this.state.opt_request_types   = opts.request_types  || [];
    }

    _buildFilters() {
        const f = {};
        if (this.state.f_team_id)       f.team_id       = this.state.f_team_id;
        if (this.state.f_equipment_id)  f.equipment_id  = this.state.f_equipment_id;
        if (this.state.f_date_from)     f.date_from     = this.state.f_date_from;
        if (this.state.f_date_to)       f.date_to       = this.state.f_date_to;
        if (this.state.f_stage_id)      f.stage_id      = this.state.f_stage_id;
        if (this.state.f_location_id)   f.location_id   = this.state.f_location_id;
        if (this.state.f_building_id)   f.building_id   = this.state.f_building_id;
        if (this.state.f_zone_id)       f.zone_id       = this.state.f_zone_id;
        if (this.state.f_floor)         f.floor         = this.state.f_floor;
        if (this.state.f_room)          f.room          = this.state.f_room;
        if (this.state.f_equipment_tag)  f.equipment_tag  = this.state.f_equipment_tag;
        if (this.state.f_request_type)   f.request_type   = this.state.f_request_type;
        return f;
    }

    // ─── Data loading ─────────────────────────────────────────────────────────

    async _loadDashboardData() {
        this.state.loading = true;
        this.state._charts.forEach(c => c.destroy());
        this.state._charts = [];

        const filters = this._buildFilters();

        const kpi = await this.orm.call("maintenance.request", "get_dashboard_data", [filters]);
        this.state.total_equipment   = kpi.total_equipment;
        this.state.total_maintenance = kpi.total_maintenance;
        this.state.maintenance_today = kpi.maintenance_today;
        this.state.overdue_requests  = kpi.overdue_requests;

        this.state.loading = false;
        setTimeout(() => this._renderAllCharts(filters), 80);
    }

    async _renderAllCharts(filters) {
        const [
            [stageCounts, stageLabels],
            [equipCounts, equipLabels],
        ] = await Promise.all([
            this.orm.call("maintenance.request", "get_requests_by_stage",     [filters]),
            this.orm.call("maintenance.request", "get_requests_by_equipment", [filters]),
        ]);

        // Cache for Excel export
        this.state._chartData = {
            stage:     { labels: stageLabels, values: stageCounts },
            equipment: { labels: equipLabels, values: equipCounts },
        };

        this._renderChart(this.stageChartRef.el, {
            type: "bar",
            data: { labels: stageLabels, datasets: [{ label: "Requests", data: stageCounts,
                backgroundColor: COLORS.slice(0, stageLabels.length), borderRadius: 6, borderSkipped: false }] },
            options: this._barOptions(),
        });

        this._renderChart(this.equipmentChartRef.el, {
            type: "bar",
            data: { labels: equipLabels, datasets: [{ label: "Requests", data: equipCounts,
                backgroundColor: COLORS.slice(0, equipLabels.length), borderRadius: 6, borderSkipped: false }] },
            options: { ...this._barOptions(), indexAxis: "y" },
        });
    }

    _renderChart(canvas, config) {
        if (!canvas) return;
        const chart = new Chart(canvas, config);
        this.state._charts.push(chart);
    }

    _barOptions(unitLabel) {
        const suffix = unitLabel ? ` ${unitLabel}` : '';
        return {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false },
                tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y ?? ctx.parsed.x}${suffix}` } } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0, color: "#6c757d" }, grid: { color: "rgba(0,0,0,.05)" } },
                x: { ticks: { color: "#6c757d" }, grid: { display: false } },
            },
        };
    }

    _lineOptions(unitLabel) {
        return {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false },
                tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y} ${unitLabel}` } } },
            scales: {
                y: { beginAtZero: true, ticks: { color: "#6c757d" }, grid: { color: "rgba(0,0,0,.05)" } },
                x: { ticks: { color: "#6c757d", maxRotation: 45 }, grid: { display: false } },
            },
        };
    }

    // ─── Event handlers ───────────────────────────────────────────────────────

    async onSearch() { await this._loadDashboardData(); }

    async onReset() {
        Object.assign(this.state, {
            f_team_id: "", f_equipment_id: "", f_date_from: "", f_date_to: "",
            f_request_type: "",
            f_stage_id: "", f_location_id: "", f_building_id: "", f_zone_id: "",
            f_floor: "", f_room: "", f_equipment_tag: "", f_request_type: "",
        });
        await this._loadDashboardData();
    }


    // ─── EXPORT: Excel ────────────────────────────────────────────────────────

    async onExportExcel() {
        this.state.exporting_excel = true;
        try {
            const XLSX = window.XLSX;
            const wb   = XLSX.utils.book_new();
            const now  = new Date().toLocaleString();

            // ── Sheet 1: KPI Summary ──────────────────────────────────────
            const kpiData = [
                ["Maintenance Dashboard — KPI Summary"],
                ["Exported:", now],
                [],
                ["KPI", "Value"],
                ["Total Equipment",   this.state.total_equipment],
                ["Total Maintenance", this.state.total_maintenance],
                ["Maintenance Today", this.state.maintenance_today],
                ["Overdue Requests",  this.state.overdue_requests],
            ];
            const wsKpi = XLSX.utils.aoa_to_sheet(kpiData);
            wsKpi['!cols'] = [{ wch: 25 }, { wch: 15 }];
            wsKpi['A1'].s = { font: { bold: true, sz: 14 } };
            XLSX.utils.book_append_sheet(wb, wsKpi, "KPI Summary");

            // ── Sheet 2: Requests by Stage ────────────────────────────────
            const d = this.state._chartData;
            this._appendChartSheet(wb, XLSX, "Requests by Stage",
                "Stage", "Requests", d.stage.labels, d.stage.values);

            // ── Sheet 3: Requests by Equipment ────────────────────────────
            this._appendChartSheet(wb, XLSX, "By Equipment",
                "Equipment", "Requests", d.equipment.labels, d.equipment.values);



            // ── Sheet 7: PPM Schedule Matrix ─────────────────────────
            await this._appendScheduleSheet(wb, XLSX);

            // Download
            const dateStr = new Date().toISOString().slice(0, 10);
            XLSX.writeFile(wb, `Maintenance_Dashboard_${dateStr}.xlsx`);
        } catch (e) {
            console.error("Excel export error:", e);
            alert("Excel export failed: " + e.message);
        } finally {
            this.state.exporting_excel = false;
        }
    }

    _appendChartSheet(wb, XLSX, sheetName, col1, col2, labels, values) {
        const rows = [[col1, col2]];
        for (let i = 0; i < labels.length; i++) {
            rows.push([labels[i], values[i]]);
        }
        const ws = XLSX.utils.aoa_to_sheet(rows);
        ws['!cols'] = [{ wch: 35 }, { wch: 20 }];
        XLSX.utils.book_append_sheet(wb, ws, sheetName);
    }

    // ─── Schedule sheet builder ──────────────────────────────────────────────

    async _appendScheduleSheet(wb, XLSX) {
        const year  = new Date().getFullYear();
        const data  = await this.orm.call(
            "maintenance.request", "get_maintenance_schedule_matrix",
            [this._buildFilters(), year]);
        const rows  = data.rows || [];

        // ── Month/week layout constants ─────────────────────────────────
        const MONTHS = [
            "January","February","March","April","May","June",
            "July","August","September","October","November","December"
        ];
        // Standard week date ranges for each month
        const WEEK_RANGES = ["1--7","8--14","15--21","22--30"];
        const INFO_COLS   = 11;   // A-L
        const WEEKS_PM    = 4;    // weeks per month
        const TOTAL_COLS  = 4;    // M / Q / A / S / TOTAL → 5 but template has 4

        // Excel column letter helper
        const colLetter = (n) => {
            let s = '';
            while (n > 0) {
                let r = (n - 1) % 26;
                s = String.fromCharCode(65 + r) + s;
                n = Math.floor((n - 1) / 26);
            }
            return s;
        };

        // First data col (M = col 13, 0-indexed = 12)
        const schedStartCol = INFO_COLS;       // 0-indexed
        const totalStartCol = schedStartCol + MONTHS.length * WEEKS_PM;  // 60
        const lastCol       = totalStartCol + 4;  // M,Q,A,S + TOTAL = 5 cols

        // ── Build AOA (array of arrays) ────────────────────────────────

        // Row 1 — headers
        const r1 = ["#","Location","Building","MODEL","Equipment Name",
                     "Equipment TAG","Room","ZONE","Floor",
                     "Asset Code","Digit Count"];
        MONTHS.forEach(mn => { r1.push(mn); r1.push("","",""); });
r1.push("TOTAL NO OF PPM PER YEAR","","","","");

        // Row 2 — week labels
        const r2 = Array(INFO_COLS).fill("");
        MONTHS.forEach((_, mi) => {
            for (let w = 1; w <= 4; w++) r2.push("W" + w);
        });
        r2.push("","","","","");

        // Row 3 — date ranges
        const r3 = Array(INFO_COLS).fill("");
        MONTHS.forEach(() => {
            WEEK_RANGES.forEach(rng => r3.push(rng));
        });
        r3.push("M","Q","A","S","TOTAL");

        const aoa = [r1, r2, r3];

        // Data rows (Excel rows 4+)
        rows.forEach((row, ri) => {
            const excelRow = ri + 4;  // 1-indexed, rows 1-3 are headers
            const dataRow  = Array(INFO_COLS).fill("");

            dataRow[0]  = row.no;
            dataRow[1]  = row.location;
            dataRow[2]  = row.building;
            dataRow[3]  = row.model;
            dataRow[4]  = row.name;
            dataRow[5]  = row.tag;
            dataRow[6]  = row.room;
            dataRow[7]  = row.zone;
            dataRow[8]  = row.floor;
                        const bc  = colLetter(2), cc = colLetter(3),
                  hc  = colLetter(8), ic = colLetter(9), fc = colLetter(6);
			dataRow[9]  = { f: `${bc}${excelRow}&${cc}${excelRow}&${hc}${excelRow}&${ic}${excelRow}&${fc}${excelRow}` };
dataRow[10] = { f: `LEN(${colLetter(10)}${excelRow})` };
            // Asset code formula: B&C&H&I&F  (same as template)
            dataRow[10] = { f: `${bc}${excelRow}&${cc}${excelRow}&${hc}${excelRow}&${ic}${excelRow}&${fc}${excelRow}` };
            dataRow[10] = { f: `LEN(${colLetter(10)}${excelRow})` };

            // 48 schedule cells (12 months × 4 weeks)
            MONTHS.forEach((_, mi) => {
                const month = mi + 1;
                for (let w = 1; w <= 4; w++) {
                    const key = `${month}_${w}`;
                    dataRow.push(row.schedule[key] || "");
                }
            });

            // TOTAL columns — COUNTIF over the 48 schedule cells
            const schedFirst = colLetter(schedStartCol + 1);  // M
            const schedLast  = colLetter(schedStartCol + 48); // BH
            const rng        = `${schedFirst}${excelRow}:${schedLast}${excelRow}`;
            dataRow.push(
                { f: `COUNTIF(${rng},"M")` },
                { f: `COUNTIF(${rng},"Q")` },
                { f: `COUNTIF(${rng},"A")` },
                { f: `COUNTIF(${rng},"S")` },
                { f: `SUM(${colLetter(totalStartCol+1)}${excelRow}:${colLetter(totalStartCol+4)}${excelRow})` }
            );

            aoa.push(dataRow);
        });

        // Empty placeholder row if no data
        if (rows.length === 0) {
            const empty = Array(lastCol).fill("");
            empty[4] = "No maintenance requests found for " + year;
            aoa.push(empty);
        }

        // ── Convert AOA to sheet ────────────────────────────────────────
        const ws = XLSX.utils.aoa_to_sheet(aoa);

        // Column widths
        ws['!cols'] = [
            { wch: 4  },   // #
            { wch: 18 },   // Location
            { wch: 16 },   // Building
            { wch: 16 },   // MODEL
            { wch: 24 },   // Equipment Name
            { wch: 14 },   // TAG
            { wch: 12 },   // Room
            { wch: 12 },   // ZONE
            { wch: 8  },   // Floor
            { wch: 20 },   // Asset Code
            { wch: 10 },   // Digit Count
        ];
        // Week columns — narrow
        for (let i = 0; i < 48; i++) ws['!cols'].push({ wch: 5 });
        // Total columns
        ws['!cols'].push({ wch: 6 },{ wch: 6 },{ wch: 6 },{ wch: 6 },{ wch: 8 });

        // Merged cells — month name spans 4 week columns
        ws['!merges'] = [];
        // Merge equipment info header rows 1-3 (rows 0-2 in 0-index)
        for (let c = 0; c < INFO_COLS; c++) {
            ws['!merges'].push({ s: { r:0, c }, e: { r:2, c } });
        }
        // Merge each month header across 4 week columns
        MONTHS.forEach((_, mi) => {
            const sc = schedStartCol + mi * 4;
            ws['!merges'].push({ s: { r:0, c: sc }, e: { r:0, c: sc+3 } });
        });
        // Merge total header across 5 cols
        ws['!merges'].push({
            s: { r:0, c: totalStartCol },
            e: { r:1, c: totalStartCol + 4 }
        });

        XLSX.utils.book_append_sheet(wb, ws, `PPM Schedule ${year}`);
    }

    // ─── EXPORT: PDF ──────────────────────────────────────────────────────────

    async onExportPdf() {
        this.state.exporting_pdf = true;
        try {
            const { jsPDF } = window.jspdf;
            const root = this.dashboardRef.el;
            if (!root) throw new Error("Dashboard element not found");

            // Snapshot the full dashboard div
            const canvas = await window.html2canvas(root, {
                scale: 1.5,
                useCORS: true,
                backgroundColor: "#f4f6fb",
                scrollX: 0,
                scrollY: -window.scrollY,
                windowWidth: root.scrollWidth,
                windowHeight: root.scrollHeight,
            });

            const imgData = canvas.toDataURL("image/jpeg", 0.92);
            const pdf     = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" });

            const pageW  = pdf.internal.pageSize.getWidth();
            const pageH  = pdf.internal.pageSize.getHeight();
            const margin = 10;
            const usableW = pageW - margin * 2;

            // Scale image to fit page width; split into pages if taller
            const ratio    = canvas.width / canvas.height;
            const imgW     = usableW;
            const imgH     = usableW / ratio;
            const totalH   = (canvas.height / canvas.width) * usableW;
            const usableH  = pageH - margin * 2;
            const pages    = Math.ceil(totalH / usableH);

            for (let p = 0; p < pages; p++) {
                if (p > 0) pdf.addPage();
                const srcY  = (p * usableH * canvas.width) / usableW;
                const sliceH = Math.min(usableH * canvas.width / usableW, canvas.height - srcY);

                // Slice canvas for this page
                const pageCanvas = document.createElement("canvas");
                pageCanvas.width  = canvas.width;
                pageCanvas.height = sliceH;
                const ctx = pageCanvas.getContext("2d");
                ctx.drawImage(canvas, 0, srcY, canvas.width, sliceH, 0, 0, canvas.width, sliceH);
                const pageImg = pageCanvas.toDataURL("image/jpeg", 0.92);

                const drawnH = (sliceH / canvas.width) * usableW;
                pdf.addImage(pageImg, "JPEG", margin, margin, usableW, drawnH);

                // Page number footer
                pdf.setFontSize(8);
                pdf.setTextColor(150);
                pdf.text(`Page ${p + 1} of ${pages}`, pageW - margin, pageH - 4, { align: "right" });
                pdf.text(`Maintenance Dashboard — ${new Date().toLocaleString()}`, margin, pageH - 4);
            }

            const dateStr = new Date().toISOString().slice(0, 10);
            pdf.save(`Maintenance_Dashboard_${dateStr}.pdf`);
        } catch (e) {
            console.error("PDF export error:", e);
            alert("PDF export failed: " + e.message);
        } finally {
            this.state.exporting_pdf = false;
        }
    }

    // ─── Tile click-through ───────────────────────────────────────────────────

    onClickEquipment() {
        const f = this._buildFilters();
        const domain = [];
        if (f.location_id)   domain.push(["location_id",   "=", parseInt(f.location_id)]);
        if (f.building_id)   domain.push(["building_id",   "=", parseInt(f.building_id)]);
        if (f.zone_id)       domain.push(["zone_id",       "=", parseInt(f.zone_id)]);
        if (f.floor)         domain.push(["floor",         "ilike", f.floor]);
        if (f.room)          domain.push(["room",          "ilike", f.room]);
        if (f.equipment_tag) domain.push(["equipment_tag", "ilike", f.equipment_tag]);
        if (f.equipment_id)  domain.push(["id",            "=", parseInt(f.equipment_id)]);
        this.action.doAction({ type: "ir.actions.act_window", name: "Filtered Equipment",
            res_model: "maintenance.equipment", views: [[false, "list"], [false, "form"]],
            target: "current", domain });
    }

onClickMaintenance() {
    const f = this._buildFilters();
    const domain = [];
    if (f.team_id)       domain.push(["maintenance_team_id",      "=",     parseInt(f.team_id)]);
    if (f.equipment_id)  domain.push(["equipment_id",             "=",     parseInt(f.equipment_id)]);
    if (f.date_from)     domain.push(["request_date",             ">=",    f.date_from]);
    if (f.date_to)       domain.push(["request_date",             "<=",    f.date_to]);
    if (f.stage_id)      domain.push(["stage_id",                 "=",     parseInt(f.stage_id)]);
    if (f.request_type)  domain.push(["request_type",             "=",     f.request_type]);
    if (f.location_id)   domain.push(["equipment_id.location_id", "=",     parseInt(f.location_id)]);
    if (f.building_id)   domain.push(["equipment_id.building_id", "=",     parseInt(f.building_id)]);
    if (f.zone_id)       domain.push(["equipment_id.zone_id",     "=",     parseInt(f.zone_id)]);
    if (f.floor)         domain.push(["equipment_id.floor",       "ilike", f.floor]);
    if (f.room)          domain.push(["equipment_id.room",        "ilike", f.room]);
    if (f.equipment_tag) domain.push(["equipment_id.equipment_tag","ilike",f.equipment_tag]);
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
        const f = this._buildFilters();
        const today = new Date().toISOString().slice(0, 10);
        const domain = [
            ["schedule_date", ">=", today + " 00:00:00"],
            ["schedule_date", "<=", today + " 23:59:59"],
        ];
        if (f.team_id)       domain.push(["maintenance_team_id",        "=",     parseInt(f.team_id)]);
        if (f.equipment_id)  domain.push(["equipment_id",               "=",     parseInt(f.equipment_id)]);
        if (f.stage_id)      domain.push(["stage_id",                   "=",     parseInt(f.stage_id)]);
        if (f.request_type)  domain.push(["request_type",               "=",     f.request_type]);
        if (f.location_id)   domain.push(["equipment_id.location_id",   "=",     parseInt(f.location_id)]);
        if (f.building_id)   domain.push(["equipment_id.building_id",   "=",     parseInt(f.building_id)]);
        if (f.zone_id)       domain.push(["equipment_id.zone_id",       "=",     parseInt(f.zone_id)]);
        if (f.floor)         domain.push(["equipment_id.floor",         "ilike", f.floor]);
        if (f.room)          domain.push(["equipment_id.room",          "ilike", f.room]);
        if (f.equipment_tag) domain.push(["equipment_id.equipment_tag", "ilike", f.equipment_tag]);
        this.action.doAction({ type: "ir.actions.act_window", name: "Maintenance Scheduled Today",
            res_model: "maintenance.request", views: [[false, "list"], [false, "form"]],
            target: "current", domain });
    }

    onClickOverdue() {
        const f = this._buildFilters();
        const now = new Date().toISOString().replace("T", " ").slice(0, 19);
        const domain = [
            ["schedule_date", "!=", false],
            ["schedule_date", "<",  now],
            
        ];
        if (f.team_id)       domain.push(["maintenance_team_id",        "=",     parseInt(f.team_id)]);
        if (f.equipment_id)  domain.push(["equipment_id",               "=",     parseInt(f.equipment_id)]);
        if (f.stage_id)      domain.push(["stage_id",                   "=",     parseInt(f.stage_id)]);
        if (f.request_type)  domain.push(["request_type",               "=",     f.request_type]);
        if (f.location_id)   domain.push(["equipment_id.location_id",   "=",     parseInt(f.location_id)]);
        if (f.building_id)   domain.push(["equipment_id.building_id",   "=",     parseInt(f.building_id)]);
        if (f.zone_id)       domain.push(["equipment_id.zone_id",       "=",     parseInt(f.zone_id)]);
        if (f.floor)         domain.push(["equipment_id.floor",         "ilike", f.floor]);
        if (f.room)          domain.push(["equipment_id.room",          "ilike", f.room]);
        if (f.equipment_tag) domain.push(["equipment_id.equipment_tag", "ilike", f.equipment_tag]);
        this.action.doAction({ type: "ir.actions.act_window", name: "Overdue Requests",
            res_model: "maintenance.request", views: [[false, "list"], [false, "form"]],
            target: "current", domain });
    }
}

registry.category("actions").add("test_dashboard", MaintenanceDashboard);
