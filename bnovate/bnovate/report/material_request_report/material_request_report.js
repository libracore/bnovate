// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Material Request Report"] = {
    filters: [
        {
            fieldname: "request_type",
            label: __("Request Type"),
            fieldtype: "Select",
            options: ["", "Material Transfer", "Purchase", "Manufacture"],
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group",
        },
        {
            "fieldname": "only_unassigned",
            "label": __("Only Unassigned"),
            "fieldtype": "Check",
            "default": 0
        }
    ],
    formatter(value, row, column, data, default_formatter) {
        if (column.fieldname === "assigned_to") {
            // return `<a >${default_formatter(date, row, col, data)}</a>`;
            return `<a onclick="assign('${data.mr_item}', '${data.assigned_to}')">${value || '<i>Unassigned</i>'}</a>`;
        }
        return default_formatter(value, row, column, data);
    }
};


async function assign(mr_item, assigned_to) {

    const fields = [{
        fieldname: "assigned_to",
        fieldtype: "Link",
        options: "User",
        label: __("Assign To"),
        default: assigned_to == 'null' ? "" : assigned_to,

    }];

    let values = await bnovate.utils.prompt("Edit dates", fields, "Confirm", "Cancel")

    if (!values) {
        return;
    }

    await frappe.db.set_value("Material Request Item", mr_item, "assigned_to", values.assigned_to);

    frappe.query_report.refresh();
}