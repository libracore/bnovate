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

        if (value && col.fieldname === 'open_sales_order') {
            let [legend, colour] = sales_order_indicator(data);
            return `<span class="indicator ${colour}">${frappe.utils.get_form_link("Sales Order", value, true, value)} [${legend}]</span>`;
        } else if (value && col.fieldname === 'work_order') {
            let [legend, colour] = work_order_indicator(data);
            return `<span class="indicator ${colour}">${frappe.utils.get_form_link("Work Order", value, true, value)} [${legend}]</span>`;
        } else if (value && col.fieldname === 'woe') {
            let [legend, colour] = work_order_entry_indicator(data);
            return `<span class="indicator ${colour}">${frappe.utils.get_form_link("Stock Entry", value, true, value)} [${legend}]</span>`;
        } else if (value && (col.fieldname === "storage_location" || col.fieldname === "storage_slot")) {
            return frappe.utils.get_form_link("Storage Location", data.storage_location_docname, true, value);
        }

        return default_formatter(value, row, col, data);
    }
};

// colours borrowed from sales_order_list.js on ERPNext app
function sales_order_indicator(doc) {
    colormap = {
        'Draft': 'darkgrey',
        'Closed': 'green',
        'On Hold': 'orange',
        'Overdue': 'red',
        'To Deliver': 'orange',
        'To Deliver and Bill': 'orange',
        'To Bill': 'orange',
        'Completed': 'green',
    }

    return [__(doc.so_status), colormap[doc.so_status]]
}


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

// Stolen from stock_entry_list.js on ERPNext 
function work_order_entry_indicator(doc) {
    if (doc.woe_docstatus === 0) {
        return [__("Draft"), "red", "docstatus,=,0"];
    } else if (doc.woe_docstatus === 2) {
        return [__("Canceled"), "red", "docstatus,=,2"];
    } else {
        return [__("Submitted"), "blue", "docstatus,=,1"];
    }
}

