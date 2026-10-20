/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const LEVEL_COLORS = {
    0: "#6c757d",
    1: "#adb5bd",
    2: "#0d6efd",
    3: "#f0ad4e",
    4: "#dc3545",
};

export class ColoredPriorityField extends Component {
    static template = "elevata_fsm_flow.ColoredPriorityField";
    static props = { ...standardFieldProps };

    get selection() {
        return this.props.record.fields[this.props.name].selection || [];
    }

    get value() {
        return this.props.record.data[this.props.name];
    }

    get selectedIndex() {
        return this.selection.findIndex((o) => o[0] === this.value);
    }

    isFilled(index) {
        return index >= 0 && index <= this.selectedIndex;
    }

    get color() {
        return LEVEL_COLORS[Number(this.value)] || "#0d6efd";
    }

    starStyle(index) {
        if (!this.isFilled(index)) {
            return "";
        }
        return `color: ${this.color};`;
    }

    onClick(value) {
        if (this.props.readonly) {
            return;
        }
        const newValue = this.value === value
            ? this.selection[0] && this.selection[0][0]
            : value;
        this.props.record.update({ [this.props.name]: newValue });
    }
}

registry.category("fields").add("elevata_priority_stars", {
    component: ColoredPriorityField,
    supportedTypes: ["selection"],
    displayName: "Priority Stars (colored)",
    isEmpty: (record, fieldName) => record.data[fieldName] === false,
});
