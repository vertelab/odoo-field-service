/** @odoo-module **/

import { onWillStart, useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";

patch(SearchBarMenu.prototype, {
    setup() {
        super.setup(...arguments);
        this.technicianOrm = useService("orm");
        this.technicianFilter = useState({ technicians: [], selectedId: false });
        onWillStart(async () => {
            if (!this.isFsmOrderSearch) {
                return;
            }
            this.technicianFilter.technicians = await this.technicianOrm.searchRead(
                "hr.employee",
                [],
                ["name"],
                { order: "name" }
            );
        });
    },

    get isFsmOrderSearch() {
        return this.env.searchModel.resModel === "fieldservice.order";
    },

    get technicianFieldItem() {
        return Object.values(this.env.searchModel.searchItems).find(
            (item) => item.type === "field" && item.fieldName === "requested_employee_ids"
        );
    },

    selectTechnician(technician) {
        const searchModel = this.env.searchModel;
        const fieldItem = this.technicianFieldItem;
        if (!fieldItem) {
            return;
        }
        const myOrders = Object.values(searchModel.searchItems).find(
            (item) => item.name === "my_orders"
        );
        if (myOrders && searchModel.query.some((query) => query.searchItemId === myOrders.id)) {
            searchModel.toggleSearchItem(myOrders.id);
        }
        searchModel.query = searchModel.query.filter(
            (query) => query.searchItemId !== fieldItem.id
        );
        if (this.technicianFilter.selectedId === technician.id) {
            this.technicianFilter.selectedId = false;
            searchModel._notify();
            return;
        }
        this.technicianFilter.selectedId = technician.id;
        searchModel.addAutoCompletionValues(fieldItem.id, {
            label: technician.name,
            operator: "=",
            value: technician.id,
        });
    },
});
