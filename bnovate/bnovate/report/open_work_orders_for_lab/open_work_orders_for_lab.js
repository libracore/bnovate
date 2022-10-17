// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Open Work Orders for Lab"] = {
	"filters": [

	],
	get_datatable_options(options) {
		return Object.assign(options, {
			dynamicRowHeight: true,
		});
	},
};
