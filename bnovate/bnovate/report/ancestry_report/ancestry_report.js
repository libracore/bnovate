// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Ancestry Report"] = {
	"filters": [
		{
			"fieldname": "batch_no",
			"label": __("Batch"),
			"fieldtype": "Link",
			"options": "Batch"
		},
		{
			"fieldname": "serial_no",
			"label": __("Serial no"),
			"fieldtype": "Link",
			"options": "Serial No"
		}
	]
};
