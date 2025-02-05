// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Accounts Payable (bN)"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		}, {
			"fieldname": "status_date",
			"label": __("Status Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	]
};
