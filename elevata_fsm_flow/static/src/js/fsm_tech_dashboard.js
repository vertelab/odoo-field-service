/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Instrumentpanel för hisstekniker.
 * Visar endast arbetsorder delegerade till inloggad tekniker —
 * ingen ekonomi, inga fakturor, inga kontrakt.
 */
export class ElevataFsmTechDashboard extends Component {
    static template = "elevata_fsm_flow.FsmTechDashboard";
    static props = { "*": true };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.user = useService("user");
        this.state = useState({
            loaded: false,
            stats: {},
            upcoming: [],
            overdueList: [],
            priorityList: [],
            shutdown: [],
            stages: [],
        });
        onWillStart(async () => {
            await this._load();
            this.state.loaded = true;
        });
    }

    get _myDomain() {
        // samma som filtret "my_orders": tekniker kopplad till inloggad användare
        return [["person_id.partner_id.user_ids", "=", this.user.userId]];
    }

    get _openDomain() {
        return [...this._myDomain, ["stage_id.is_closed", "=", false]];
    }

    async _load() {
        const Order = "fieldservice.order";
        const Loc = "maintenance.equipment";
        const now = new Date().toISOString().slice(0, 19).replace("T", " ");
        const today = new Date().toISOString().slice(0, 10);
        const t = new Date();
        const tomorrow = new Date(t.getTime() + 864e5).toISOString().slice(0, 10);
        // denna vecka: idag → söndag
        const dow = (t.getDay() + 6) % 7; // mån=0
        const endWeek = new Date(t.getTime() + (6 - dow) * 864e5)
            .toISOString().slice(0, 10);

        const [open, todayCount, tomorrowCount, weekCount, overdue,
               unscheduled, done, shutdownCount, priorityCount] =
            await Promise.all([
                this.orm.searchCount(Order, this._openDomain),
                this.orm.searchCount(Order, [
                    ...this._myDomain,
                    ["planned_start_datetime", ">=", today + " 00:00:00"],
                    ["planned_start_datetime", "<=", today + " 23:59:59"],
                ]),
                this.orm.searchCount(Order, [
                    ...this._myDomain,
                    ["planned_start_datetime", ">=", tomorrow + " 00:00:00"],
                    ["planned_start_datetime", "<=", tomorrow + " 23:59:59"],
                ]),
                this.orm.searchCount(Order, [
                    ...this._myDomain,
                    ["planned_start_datetime", ">=", today + " 00:00:00"],
                    ["planned_start_datetime", "<=", endWeek + " 23:59:59"],
                ]),
                this.orm.searchCount(Order, [
                    ...this._openDomain,
                    ["planned_start_datetime", "<", now],
                ]),
                this.orm.searchCount(Order, [
                    ...this._openDomain,
                    ["planned_start_datetime", "=", false],
                ]),
                this.orm.searchCount(Order, [
                    ...this._myDomain,
                    ["stage_id.is_closed", "=", true],
                ]),
                this.orm.searchCount(Loc,
                    [["operational_status", "=", "out_of_order"]]),
                this.orm.searchCount(Order, [
                    ...this._openDomain,
                    ["priority", "in", ["3", "4"]],
                ]),
            ]);
        this.state.stats = {
            open, today: todayCount, tomorrow: tomorrowCount,
            week: weekCount, overdue, unscheduled, done,
            shutdown: shutdownCount, priority: priorityCount,
        };

        // pipeline per status — samma som fieldservice-dashboarden,
        // men filtrerat på teknikerns egna ordrar
        const stageGroups = await this.orm.readGroup(
            Order, this._myDomain, ["stage_id"], ["stage_id"]
        );
        this.state.stages = stageGroups
            .filter((g) => g.stage_id_count > 0)
            .map((g) => ({
                id: g.stage_id ? g.stage_id[0] : false,
                name: g.stage_id ? g.stage_id[1] : "Ingen status",
                count: g.stage_id_count || 0,
            }));

        this.state.shutdown = await this.orm.searchRead(
            Loc,
            [["operational_status", "=", "out_of_order"]],
            ["name", "out_of_order_reason", "out_of_order_date"],
            { limit: 8 }
        );
        this.state.priorityList = await this.orm.searchRead(
            Order,
            [...this._openDomain, ["priority", "in", ["3", "4"]]],
            ["name", "equipment_id", "product_type", "priority", "planned_start_datetime"],
            { limit: 8, order: "priority desc, planned_start_datetime asc" }
        );

        this.state.upcoming = await this.orm.searchRead(
            Order,
            [...this._openDomain, ["planned_start_datetime", ">=", now]],
            ["name", "equipment_id", "product_type", "priority", "planned_start_datetime"],
            { limit: 10, order: "planned_start_datetime asc" }
        );
        this.state.overdueList = await this.orm.searchRead(
            Order,
            [...this._openDomain, ["planned_start_datetime", "<", now]],
            ["name", "equipment_id", "product_type", "priority", "planned_start_datetime"],
            { limit: 10, order: "planned_start_datetime asc" }
        );
    }

    fmt(v) {
        return v ? v.slice(0, 16).replace("T", " ") : "";
    }

    _open(name, domain, views) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "fieldservice.order",
            views: views || [[false, "kanban"], [false, "list"], [false, "form"]],
            domain,
            target: "current",
        });
    }

    openMyOpen() { this._open("Mina öppna ordrar", this._openDomain); }
    openStage(st) {
        this._open("Mina ordrar — " + st.name, [
            ...this._myDomain,
            st.id ? ["stage_id", "=", st.id] : ["stage_id", "=", false],
        ]);
    }
    openToday() {
        const d = new Date().toISOString().slice(0, 10);
        this._open("Mina ordrar idag", [
            ...this._myDomain,
            ["planned_start_datetime", ">=", d + " 00:00:00"],
            ["planned_start_datetime", "<=", d + " 23:59:59"],
        ], [[false, "list"], [false, "kanban"], [false, "form"]]);
    }
    openOverdue() {
        const now = new Date().toISOString().slice(0, 19).replace("T", " ");
        this._open("Mina försenade ordrar", [
            ...this._openDomain,
            ["planned_start_datetime", "<", now],
        ], [[false, "list"], [false, "kanban"], [false, "form"]]);
    }
    openUnscheduled() {
        this._open("Mina oschemalagda ordrar", [
            ...this._openDomain,
            ["planned_start_datetime", "=", false],
        ]);
    }
    openTomorrow() {
        const t = new Date();
        const d = new Date(t.getTime() + 864e5).toISOString().slice(0, 10);
        this._open("Mina ordrar imorgon", [
            ...this._myDomain,
            ["planned_start_datetime", ">=", d + " 00:00:00"],
            ["planned_start_datetime", "<=", d + " 23:59:59"],
        ], [[false, "list"], [false, "kanban"], [false, "form"]]);
    }
    openWeek() {
        const t = new Date();
        const today = t.toISOString().slice(0, 10);
        const dow = (t.getDay() + 6) % 7;
        const end = new Date(t.getTime() + (6 - dow) * 864e5)
            .toISOString().slice(0, 10);
        this._open("Mina ordrar denna vecka", [
            ...this._myDomain,
            ["planned_start_datetime", ">=", today + " 00:00:00"],
            ["planned_start_datetime", "<=", end + " 23:59:59"],
        ], [[false, "list"], [false, "kanban"], [false, "form"]]);
    }
    openPriority() {
        this._open("Mina prioriterade ordrar", [
            ...this._openDomain,
            ["priority", "in", ["3", "4"]],
        ]);
    }
    openShutdown() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Avstängda hissar",
            res_model: "maintenance.equipment",
            views: [[false, "list"], [false, "form"]],
            domain: [["operational_status", "=", "out_of_order"]],
            target: "current",
        });
    }
    openLocation(rec) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "maintenance.equipment",
            res_id: rec.id,
            views: [[false, "form"]],
            target: "current",
        });
    }
    openDone() {
        this._open("Mina avslutade ordrar", [
            ...this._myDomain,
            ["stage_id.is_closed", "=", true],
        ]);
    }
    openOrder(rec) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "fieldservice.order",
            res_id: rec.id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("elevata_fsm_tech_dashboard", ElevataFsmTechDashboard);
