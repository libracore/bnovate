// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Connectivity Data Usage"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			// "default": frappe.datetime.month_end(),
		},
		{
			"fieldname": "connectivity_package",
			"label": __("Connectivity Package"),
			"fieldtype": "Link",
			"options": "Connectivity Package"
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
	]
};
