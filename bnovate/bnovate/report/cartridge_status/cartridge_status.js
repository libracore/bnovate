// Copyright (c) 2023, bnovate, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Cartridge Status"] = {
    filters: [
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "serial_no",
            "label": __("Serial No"),
            "fieldtype": "Link",
            "options": "Serial No"
        },
        {
            "fieldname": "only_stored",
            "label": __("At bNovate only"),
            "fieldtype": "Check",
            "default": 0
        },
    ],
    formatter(value, row, col, data, default_formatter) {

        if (value && col.fieldname === 'work_order') {
            let [legend, colour] = work_order_indicator(data);
            return `<span class="indicator ${colour}">${frappe.utils.get_form_link("Work Order", value, true, value)} [${legend}]</span>`;
        } else if (value && col.fieldname === 'woe') {
            let [legend, colour] = work_order_entry_indicator(data);
            return `<span class="indicator ${colour}">${frappe.utils.get_form_link("Stock Entry", value, true, value)} [${legend}]</span>`;
        }

        return default_formatter(value, row, col, data);
    }
};


// Stolen from work_order_list.js on ERPNext 
function work_order_indicator(doc) {
    if (doc.wo_status === "Submitted") {
        return [__("Not Started"), "orange"];
    } else {
        return [__(doc.wo_status), {
            "Draft": "red",
            "Stopped": "red",
            "Not Started": "red",
            "In Process": "orange",
            "Completed": "green",
            "Cancelled": "darkgrey"
        }[doc.wo_status]];
    }
}

function work_order_entry_indicator(doc) {
    if (doc.woe_docstatus === 0) {
        return [__("Draft"), "red", "docstatus,=,0"];
    } else if (doc.woe_docstatus === 2) {
        return [__("Canceled"), "red", "docstatus,=,2"];
    } else {
        return [__("Submitted"), "blue", "docstatus,=,1"];
    }
}

