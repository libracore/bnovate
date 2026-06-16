// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Breakbulk Data Export"] = {
	filters: [
		{
			"fieldname": "date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 0
		}, {
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		}
	],
	onload(report) {
		this.report = report;
		report.page.add_inner_button(__('<i class="fa fa-download"></i> Export to CSV'), () => {
			const column_row = this.report.columns.map(col => col.label);
			const data = this.report.get_data_for_csv();
			const out = [column_row].concat(data);

			frappe.tools.downloadify(out, null, this.report.report_name);
		});

		report.page.add_inner_button(__('<i class="fa fa-download"></i> Commercial Invoices'), () => {
			const dn_list = Array.from(new Set(frappe.query_report.data.map(row => row.dn_name)));
			bnovate.utils.open_pdf_urls("Delivery Note", dn_list, "Commercial Invoice CHF");
		});
	},
};
