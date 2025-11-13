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
            fieldname: "assigned_to",
            label: __("Assigned To"),
            fieldtype: "Link",
            options: "User",
        },
        {
            "fieldname": "only_unassigned",
            "label": __("Only Unassigned"),
            "fieldtype": "Check",
            "default": 0
        }
    ],
    formatter(value, row, col, data, default_formatter) {
        if (col.fieldname === "assigned_to") {
            // return `<a >${default_formatter(date, row, col, data)}</a>`;
            return `<a onclick="assign('${data.mr_item}', '${data.assigned_to}')">${value || '<i>Unassigned</i>'}</a>`;
        } else if (col.fieldname === 'purchase_order') {
            if (value) {

                let [legend, colour] = purchase_order_indicator(data);
                return `<span class="indicator ${colour}">${frappe.utils.get_form_link("Purchase Order", value, true, value)} [${legend}]</span>`;
            } else {
                return `<button class="btn btn-xs btn-primary create-po" onclick="create_po('${data.supplier}')">Create PO</button>`;
            }
        }
        return default_formatter(value, row, col, data);
    }
};

// colours borrowed from sales_order_list.js on ERPNext app
function purchase_order_indicator(doc) {
    colormap = {
        "Draft": "red",
        "Closed": "green",
        "On Hold": "orange",
        "Delivered": "green",
        "To Receive and Bill": "orange",
        "To Receive": "orange",
        "To Bill": "orange",
        "Completed": "green"
    }
    return [__(doc.po_status), colormap[doc.po_status]]
}


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

async function create_po(supplier) {

    // Create PO for all open MRs for the same supplier
    const resp = await frappe.call({
        method: "erpnext.stock.doctype.material_request.material_request.make_purchase_order_based_on_supplier",
        args: { source_name: supplier }
    });

    // const doc = frappe.get_doc(resp.message);
    const doc = resp.message;

    // Setting price list rate from BKO works, but amount is overriden by a link trigger - just let it be calculated on save.
    doc.items.forEach(i => {
        if (i.blanket_order) {
            i.price_list_rate = i.blanket_order_rate;
        }
    });
    frappe.model.sync(doc);
    frappe.set_route("Form", doc.doctype, doc.name);
}