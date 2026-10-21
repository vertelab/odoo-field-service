/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formatFloat } from "@web/views/fields/formatters";
import { WithSearch } from "@web/search/with_search/with_search";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";

export class DashboardSearch extends Component {
    static template = "elevata_fsm_flow.DashboardSearch";
    static components = { SearchBar, SearchBarMenu };
    static props = { "*": true };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.searchModel = this.env.searchModel;
        this.state = useState({ searched: false, orders: [], groups: [] });
        const update = () => this._run();
        this.searchModel.addEventListener("update", update);
        onWillStart(update);
    }

    async _run() {
        const domain = this.searchModel.domain;
        const groupBy = this.searchModel.groupBy || [];
        if (!domain.length && !groupBy.length) {
            this.state.searched = false;
            this.state.orders = [];
            this.state.groups = [];
            return;
        }
        this.state.searched = true;
        if (groupBy.length) {
            const field = groupBy[0].split(":")[0];
            const groups = await this.orm.readGroup(
                "fieldservice.order", domain, [field], [field]
            );
            this.state.groups = groups.map((g) => {
                const v = g[field];
                return {
                    name: v ? (Array.isArray(v) ? v[1] : String(v)) : "Saknas",
                    count: g[`${field}_count`] || 0,
                    domain: g.__domain,
                };
            });
            this.state.orders = [];
        } else {
            this.state.groups = [];
            this.state.orders = await this.orm.searchRead(
                "fieldservice.order", domain,
                ["name", "equipment_id", "product_type", "stage_id"],
                { limit: 20 }
            );
        }
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

    openGroup(group) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Ordrar: " + group.name,
            res_model: "fieldservice.order",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain: group.domain,
            target: "current",
        });
    }

    openAll() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Arbetsorder",
            res_model: "fieldservice.order",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: this.searchModel.domain,
            target: "current",
        });
    }
}

export class ElevataFsmDashboard extends Component {
    static template = "elevata_fsm_flow.FsmDashboard";
    static components = { WithSearch, DashboardSearch };
    static props = { "*": true };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loaded: false, stats: {}, urgent: [], shutdown: [], stages: [], repeatLocs: [], planned: [],
        });
        onWillStart(async () => {
            await this._load();
            this.state.loaded = true;
        });
    }

    async _load() {
        const s = {};
        const openDomain = [["stage_id.is_closed", "=", false]];
        const Order = "fieldservice.order";
        const Loc = "maintenance.equipment";

        const now = new Date().toISOString().slice(0, 19).replace("T", " ");
        const [openCount, critical, high, toInvoice, shutdown, today, invMonth,
               overdue, unassigned, inspectionNotes, contracts] =
            await Promise.all([
                this.orm.searchCount(Order, openDomain),
                this.orm.searchCount(Order, [...openDomain, ["priority", "=", "4"]]),
                this.orm.searchCount(Order, [...openDomain, ["priority", "=", "3"]]),
                this.orm.searchCount(Order, [["account_stage", "=", "confirmed"]]),
                this.orm.searchCount(Loc, [["operational_status", "=", "out_of_order"]]),
                this._ordersToday(),
                this._invoicesThisMonth(),
                this.orm.searchCount(Order, [...openDomain, ["planned_start_datetime", "<", now]]),
                this.orm.searchCount(Order, [...openDomain, ["requested_employee_ids", "=", false]]),
                this.orm.searchCount(Order, [...openDomain, ["product_type.name", "ilike", "anmärk"]]),
                this.orm.searchCount("elevata.service.contract", [["state", "=", "confirmed"]]),
            ]);

        Object.assign(s, { openCount, critical, high, toInvoice, shutdown, today,
                           overdue, unassigned, inspectionNotes, contracts });
        s.invMonth = invMonth;
        this.state.stats = s;

        // Pipeline: ordrar per status (alla statusar, inkl. stängda)
        const stageGroups = await this.orm.readGroup(
            Order, [], ["stage_id"], ["stage_id"]
        );
        this.state.stages = stageGroups.filter((g) => g.stage_id_count > 0).map((g) => ({
            id: g.stage_id ? g.stage_id[0] : false,
            name: g.stage_id ? g.stage_id[1] : "Ingen status",
            count: g.stage_id_count || 0,
            domain: g.__domain,
        }));

        this.state.urgent = await this.orm.searchRead(
            Order,
            [...openDomain, ["priority", "in", ["3", "4"]]],
            ["name", "equipment_id", "priority", "product_type", "planned_start_datetime"],
            { limit: 8, order: "priority desc, planned_start_datetime asc" }
        );
        this.state.shutdown = await this.orm.searchRead(
            Loc,
            [["operational_status", "=", "out_of_order"]],
            ["name", "out_of_order_reason", "out_of_order_date"],
            { limit: 8 }
        );

        // Återkommande problem: hissar med flest ordrar senaste 30 dagarna
        const d = new Date();
        d.setDate(d.getDate() - 30);
        const since = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
        const [locGroups, locOpenGroups] = await Promise.all([
            this.orm.readGroup(
                Order,
                [["create_date", ">=", since], ["equipment_id", "!=", false]],
                ["equipment_id"],
                ["equipment_id"],
                { orderby: "equipment_id_count desc", limit: 8 }
            ),
            this.orm.readGroup(
                Order,
                [["create_date", ">=", since], ["equipment_id", "!=", false],
                 ["stage_id.is_closed", "=", false]],
                ["equipment_id"],
                ["equipment_id"]
            ),
        ]);
        const openByLoc = {};
        for (const g of locOpenGroups) {
            openByLoc[g.equipment_id[0]] = g.equipment_id_count;
        }
        this.state.repeatLocs = locGroups
            .filter((g) => g.equipment_id_count > 0)
            .map((g) => ({
                id: g.equipment_id[0],
                name: g.equipment_id[1],
                count: g.equipment_id_count,
                open: openByLoc[g.equipment_id[0]] || 0,
            }));

        // Planering: kommande planerade ordrar
        this.state.planned = await this.orm.searchRead(
            Order,
            [["stage_id.is_closed", "=", false],
             ["planned_start_datetime", ">=", now]],
            ["name", "equipment_id", "requested_employee_ids", "product_type", "planned_start_datetime"],
            { limit: 10, order: "planned_start_datetime asc" }
        );
    }

    formatPlanned(rec) {
        const v = rec.planned_start_datetime;
        return v ? v.slice(0, 16).replace("T", " ") : "";
    }

    async _ordersToday() {
        const today = new Date();
        const d = today.toISOString().slice(0, 10);
        return this.orm.searchCount("fieldservice.order", [
            ["planned_start_datetime", ">=", d + " 00:00:00"],
            ["planned_start_datetime", "<=", d + " 23:59:59"],
        ]);
    }

    async _invoicesThisMonth() {
        const now = new Date();
        const first = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
        const groups = await this.orm.readGroup(
            "account.move",
            [
                ["move_type", "=", "out_invoice"],
                ["state", "=", "posted"],
                ["invoice_date", ">=", first],
            ],
            ["amount_total:sum"],
            []
        );
        const g = groups[0] || {};
        const sum = g.amount_total || 0;
        return {
            count: g.__count || 0,
            total: `${formatFloat(sum, { digits: [16, 0] })} kr`,
        };
    }

    _open(model, name, domain, views) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: model,
            views: views || [[false, "list"], [false, "form"]],
            domain,
            target: "current",
        });
    }

    openOpenOrders() {
        this._open("fieldservice.order", "Öppna arbetsorder",
            [["stage_id.is_closed", "=", false]],
            [[false, "kanban"], [false, "list"], [false, "form"]]);
    }
    openCritical() {
        this._open("fieldservice.order", "Kritiska ordrar",
            [["stage_id.is_closed", "=", false], ["priority", "=", "4"]],
            [[false, "kanban"], [false, "list"], [false, "form"]]);
    }
    openHigh() {
        this._open("fieldservice.order", "Hög prioritet",
            [["stage_id.is_closed", "=", false], ["priority", "=", "3"]],
            [[false, "kanban"], [false, "list"], [false, "form"]]);
    }
    openToday() {
        const d = new Date().toISOString().slice(0, 10);
        this._open("fieldservice.order", "Ordrar idag",
            [["planned_start_datetime", ">=", d + " 00:00:00"],
             ["planned_start_datetime", "<=", d + " 23:59:59"]],
            [[false, "list"], [false, "kanban"], [false, "form"]]);
    }
    openToInvoice() {
        this._open("fieldservice.order", "Att fakturera",
            [["account_stage", "=", "confirmed"]],
            [[false, "list"], [false, "form"]]);
    }
    openOverdue() {
        const now = new Date().toISOString().slice(0, 19).replace("T", " ");
        this._open("fieldservice.order", "Försenade ordrar",
            [["stage_id.is_closed", "=", false], ["planned_start_datetime", "<", now]],
            [[false, "list"], [false, "kanban"], [false, "form"]]);
    }
    openUnassigned() {
        this._open("fieldservice.order", "Otilldelade ordrar",
            [["stage_id.is_closed", "=", false], ["requested_employee_ids", "=", false]],
            [[false, "kanban"], [false, "list"], [false, "form"]]);
    }
    openInspectionNotes() {
        this._open("fieldservice.order", "Besiktningsanmärkningar",
            [["stage_id.is_closed", "=", false], ["product_type.name", "ilike", "anmärk"]],
            [[false, "kanban"], [false, "list"], [false, "form"]]);
    }
    openContracts() {
        this._open("elevata.service.contract", "Aktiva serviceavtal",
            [["state", "=", "confirmed"]]);
    }
    openStage(stage) {
        this._open("fieldservice.order", "Ordrar: " + stage.name,
            stage.domain || [["stage_id", "=", stage.id]],
            [[false, "kanban"], [false, "list"], [false, "form"]]);
    }
    openShutdown() {
        this._open("maintenance.equipment", "Avstängda hissar",
            [["operational_status", "=", "out_of_order"]]);
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
    openLocation(rec) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "maintenance.equipment",
            res_id: rec.id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("elevata_fsm_dashboard", ElevataFsmDashboard);
