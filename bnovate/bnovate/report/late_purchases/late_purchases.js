// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Late Purchases"] = {
	filters: [
		{
			"fieldname": "bnovate_contact",
			"label": __("bNovate Contact"),
			"fieldtype": "Link",
			"options": "User",
		}
	]
};
