// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Subscriptions Billable"] = {
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
		'method': "bnovate.bnovate.report.subscriptions_billable.subscriptions_billable.create_invoice",
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