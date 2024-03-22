// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Weekly Sales"] = {
	"filters": [{
		"fieldname": "company",
		"label": __("Company"),
		"fieldtype": "Link",
		"options": "Company",
		"default": frappe.defaults.get_default("Company"),
	},
	{
		"fieldname": "only_current_fy",
		"label": __("Only current year"),
		"fieldtype": "Check",
		"default": 1
	}]
};
