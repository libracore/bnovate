// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Orders to Fulfill"] = {
	filters: [
		{
			"fieldname": "only_manufacturing",
			"label": __("Only manufactured items"),
			"fieldtype": "Check",
			"default": 1
		},
		{
			"fieldname": "include_drafts",
			"label": __("Include Drafts"),
			"fieldtype": "Check",
			"default": 0
		}
	],
	initial_depth: 0,
	onload(report) {
		this.report = report;
		this.week_index = 1;
		this.date_index = 1;
		this.colours = ["light", "dark"];
	},
	formatter(value, row, col, data, default_formatter) {
		// Keep only qty and item code for packed items.
		if (data.indent === 1 && ['remaining_qty', 'item_code'].indexOf(col.fieldname) < 0) {
			return "";
		}
		if (col.fieldname === "weeknum") {
			return `<span class="coloured ${this.colours[data.week_index % this.colours.length]}">${default_formatter(value, row, col, data)}</span>`;
		}
		if (col.fieldname === "sales_order" || col.fieldname === "customer" || col.fieldname === "customer_name") {
			return `<span class="coloured ${this.colours[data.so_index % this.colours.length]}">${default_formatter(value, row, col, data)}</span>`;
		}
		if (col.fieldname === "ship_date") {
			return `<span class="coloured ${this.colours[data.day_index % this.colours.length]}">${default_formatter(value, row, col, data)}</span>`;
		}
		return default_formatter(value, row, col, data);
	}
};
