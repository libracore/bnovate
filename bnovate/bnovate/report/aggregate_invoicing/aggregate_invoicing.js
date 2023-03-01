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
        console.log("Report:", report);
        this.report = report;
        this.ref_index = 1;
        this.bp_index = 1; // billing period
        this.colours = ["#e5e5e5", "#f7f7f7"];
        this.colours = ["light", "dark"];
    },
    formatter(value, row, col, data, default_formatter) {
        if (data.indent == 0) {
            return '<b>' + default_formatter(value, row, col, data) + "</b>";
        }

        // If we've reached this point, row is > 0
        if (col.fieldname == "reference") {
            console.log("reference", row, col, this.colours[this.ref_index % this.colours.length])
            // Cycle colours if previous row has difference reference
            if (this.report.data[row[0].rowIndex - 1].reference != data.reference) {
                this.ref_index += 1
            }
            return `<span class="coloured ${this.colours[this.ref_index % this.colours.length]}">${default_formatter(value, row, col, data)}</span>`
        } else if (col.fieldname == "date") {
            if (this.report.data[row[0].rowIndex - 1].date != data.date) {
                this.bp_index += 1
            }
            return `<span class="coloured ${this.colours[this.bp_index % this.colours.length]}">${default_formatter(value, row, col, data)}</span>`
        } else if (col.fieldname == "period_end") {
            return `<span class="coloured ${this.colours[this.bp_index % this.colours.length]}">${default_formatter(value, row, col, data)}</span>`
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