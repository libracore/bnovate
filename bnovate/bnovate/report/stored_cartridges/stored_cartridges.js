// Copyright (c) 2023, bnovate, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stored Cartridges"] = {
	"filters": [
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		}
	]
};
