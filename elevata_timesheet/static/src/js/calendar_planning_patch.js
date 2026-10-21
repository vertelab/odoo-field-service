/** @odoo-module **/

import { AttendeeCalendarCommonRenderer } from "@calendar/views/attendee_calendar/common/attendee_calendar_common_renderer";
import { AttendeeCalendarCommonPopover } from "@calendar/views/attendee_calendar/common/attendee_calendar_common_popover";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

const DEFAULT_COLORS = {
    "2": { bg: "#27ae60", border: "#1e8449", text: "#ffffff", allBorder: false },
    "3": { bg: "#e74c3c", border: "#a93226", text: "#ffffff", allBorder: false },
    "1": { bg: "#3498db", border: "#2176ad", text: "#ffffff", allBorder: true },
    "8": { bg: "#bdc3c7", border: "#95a5a6", text: "#333333", allBorder: true },
};

let _colorConfigCache = DEFAULT_COLORS;

patch(AttendeeCalendarCommonRenderer.prototype, {
    onEventRender(info) {
        super.onEventRender(...arguments);

        const { el } = info;
        const record = this.props.model.records[info.event.id];
        if (!record) return;

        const elevataColor = record.rawRecord.elevata_color;
        const colors = _colorConfigCache[String(elevataColor)];
        if (!colors) return;

        const fcBg = el.querySelector(".fc-bg");
        if (fcBg) {
            fcBg.style.setProperty("background-color", colors.bg, "important");
        }
        el.style.setProperty("background-color", colors.bg, "important");
        el.style.setProperty("color", colors.text, "important");

        if (colors.allBorder) {
            el.style.setProperty("border", `2px solid ${colors.border}`, "important");
            el.style.setProperty("border-radius", "3px", "important");
        } else {
            el.style.setProperty("border-color", colors.border, "important");
        }

        const fcContent = el.querySelector(".fc-content");
        if (fcContent) {
            fcContent.style.setProperty("color", colors.text, "important");
        }
    },
});

patch(AttendeeCalendarCommonPopover.prototype, {
    setup() {
        super.setup(...arguments);
        this.elevataAction = useService("action");
        this.elevataRpc = useService("rpc");
    },

    get hasFsmOrder() {
        const raw = this.props.record.rawRecord;
        return !!(raw.elevata_fsm_order_id && raw.elevata_fsm_order_id[0]);
    },

    get isPlanningEvent() {
        const raw = this.props.record.rawRecord;
        const color = raw.elevata_color;
        return color === 2 || color === 3;
    },

    openFsmOrder() {
        const raw = this.props.record.rawRecord;
        const orderId = raw.elevata_fsm_order_id && raw.elevata_fsm_order_id[0];
        if (!orderId) return;
        this.props.close();
        this.elevataAction.doAction({
            type: "ir.actions.act_window",
            res_model: "fsm.order",
            res_id: orderId,
            views: [[false, "form"]],
            target: "current",
        });
    },

    async convertToTimesheet() {
        const eventId = this.props.record.id;
        if (!eventId) return;
        const planningIds = await this.elevataRpc(
            "/web/dataset/call_kw/elevata.fsm.planning/search_read",
            {
                model: "elevata.fsm.planning",
                method: "search_read",
                args: [[["calendar_event_id", "=", eventId]], ["id"]],
                kwargs: { limit: 1 },
            }
        );
        if (!planningIds || !planningIds.length) return;
        await this.elevataRpc(
            "/web/dataset/call_kw/elevata.fsm.planning/action_convert_to_timesheet",
            {
                model: "elevata.fsm.planning",
                method: "action_convert_to_timesheet",
                args: [[planningIds[0].id]],
                kwargs: {},
            }
        );
        this.props.close();
        this.props.model.load();
    },
});
