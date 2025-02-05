// Copyright (c) 2025, libracore, bNovate and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Accounts Receivable (bN)"] = {
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
