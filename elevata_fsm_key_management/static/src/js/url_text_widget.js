/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

class UrlTextField extends Component {
    static template = "elevata_fsm_key_management.UrlTextField";
    static props = {
        ...standardFieldProps,
        urlField: { type: String, optional: true },
    };

    get url() {
        const data = this.props.record.data;
        const address = (this.props.urlField && data[this.props.urlField])
            || data[this.props.name];
        if (!address) return '';
        const params = {
            api: '1',
            destination: address,
        };
        return 'https://www.google.com/maps/dir/?' + new URLSearchParams(params).toString();
    }

    get displayValue() {
        return this.props.record.data[this.props.name] || '';
    }

    onClick() {
        if (this.url) {
            window.open(this.url, '_blank');
        }
    }
}

export const urlTextField = {
    component: UrlTextField,
    supportedTypes: ["char", "text"],
    extractProps: ({ attrs, options }) => ({
        name: attrs.name,
        urlField: options && options.url_field,
    }),
};

registry.category("fields").add("url_text", urlTextField);
