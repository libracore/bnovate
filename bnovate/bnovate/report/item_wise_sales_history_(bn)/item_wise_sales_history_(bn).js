// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item-wise Sales History (bN)"] = {
	"filters": [
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "MultiSelectList",
			get_data: function () {
				// return a Promise that resolves to the options array
				return [
					{ value: "Draft", description: "Draft" },
					{ value: "On Hold", description: "On Hold" },
					{ value: "To Deliver and Bill", description: "To Deliver and Bill" },
					{ value: "To Bill", description: "To Bill" },
					{ value: "To Deliver", description: "To Deliver" },
					{ value: "Completed", description: "Completed" },
					{ value: "Cancelled", description: "Cancelled" }
				];
			},
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "filter_on_date",
			label: __("Filter on"),
			fieldtype: "Select",
			options: [
				{ label: "Sales Order Date", value: "transaction_date" },
				{ label: "Delivery Date", value: "delivery_date" },
			],
			default: "transaction_date",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company")
		},
	]
};
