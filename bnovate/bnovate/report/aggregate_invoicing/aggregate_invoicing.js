// Copyright (c) 2023, bNovate, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Aggregate Invoicing"] = {
    filters: [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date"
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date"
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "show_invoiced",
            "label": __("Show Invoiced Periods"),
            "fieldtype": "Check",
            "default": 0
        },
    ],
    initial_depth: 1,
    onload(report) {
        // console.log("Report:", report);
    },
    formatter(value, row, col, data, default_formatter) {
        if (row[0].indent == 0) {
            return '<b>' + default_formatter(value, row, col, data) + "</b>";
        }
        return default_formatter(value, row, col, data);
    }
};


function create_invoice(customer) {
    frappe.call({
        'method': "bnovate.bnovate.report.aggregate_invoicing.aggregate_invoicing.create_invoice",
        'args': {
            'from_date': frappe.query_report.filters[0].value,
            'to_date': frappe.query_report.filters[1].value,
            'customer': customer,
        },
        'callback': function (response) {
            frappe.show_alert(__("Created") + ": <a href='/desk#Form/Sales Invoice/" + response.message
                + "'>" + response.message + "</a>");
            frappe.query_report.refresh();
        }
    });
}