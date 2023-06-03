// Copyright (c) 2023, bNovate, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Recently Returned Cartridges"] = {
    filters: [

    ],
    formatter(value, row, col, data, default_formatter) {
        if (value && col.fieldname === 'open_sales_order') {
            let [legend, colour] = sales_order_indicator(data);
            return `<span class="indicator ${colour}">${frappe.utils.get_form_link("Sales Order", value, true, value)} [${legend}]</span>`;
        }
        return default_formatter(value, row, col, data);
    },
};


// colours borrowed from sales_order_list.js on ERPNext app
function sales_order_indicator(doc) {
    colormap = [
        ['Draft', 'red'],
        ['Submitted', 'orange'],
        ['Cancelled', 'darkgrey'],
    ];

    return colormap[doc.open_sales_order_docstatus || 0];
}