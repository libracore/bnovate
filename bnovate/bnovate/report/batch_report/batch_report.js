// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Batch Report"] = {
	"filters": [{
		fieldname: "item_code",
		label: __("Item Code"),
		fieldtype: "Link",
		options: "Item"
	}, {
		fieldname: "warehouse",
		label: __("Warehouse"),
		fieldtype: "Link",
		options: "Warehouse"
	}, {
		fieldname: "expires_in_days",
		label: __("Expires In Max (Days)"),
		fieldtype: "Int",
	}, {
		fieldname: "status_date",
		label: __("As of Date"),
		fieldtype: "Date",
		default: frappe.datetime.get_today()
	}, {
		fieldname: "only_in_stock",
		label: __("Only Batches in Stock"),
		fieldtype: "Check",
		default: 1
	}]
};
