// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */


frappe.require("/assets/bnovate/js/modals.js")  // provides bnovate.modals

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
		},
		{
			"fieldname": "sales_order",
			"label": __("Sales Order"),
			"fieldtype": "Link",
			"options": "Sales Order",
			"default": 0
		}
	],
	initial_depth: 0,
	onload(report) {
		this.report = report;
		this.week_index = 1;
		this.date_index = 1;
		this.colours = ["light", "dark"];


		report.page.add_inner_button(__('Toggle Chart'), () => {
			if (this.report.$chart.is(':visible')) {
				this.report.$chart.hide();
			} else {
				this.report.$chart.show();
			}
		})

		bnovate.modals.attach_report_modal("cartStatusModal");
	},
	after_datatable_render(datatable) {
		// Activate tooltips on columns
		$(function () {
			$('[data-toggle="tooltip"]').tooltip()
		})
	},
	formatter(value, row, col, data, default_formatter) {
		if (col.fieldname === "sufficient_stock" && typeof value !== 'undefined') {
			let color = ['red', 'orange', 'yellow', 'green'][value];
			return `<span class="indicator ${color}"></span>`;
		}
		// Keep only a few columns for packed items.
		if (data.indent === 1 && ['remaining_qty', 'item_code', 'projected_stock', 'guaranteed_stock', 'work_order'].indexOf(col.fieldname) < 0) {
			return "";
		}
		if (col.fieldname === "work_order" && data.work_order) {
			if (data.work_order_acc) {
				return data.work_order_acc.map(r => {
					let [legend, colour] = work_order_indicator(r);
					return ` <span class="indicator ${colour}">${frappe.utils.get_form_link("Work Order", r.work_order, true)}</span> (${r.wo_produced_qty}/${r.wo_qty})`;
				}).join(", ");
			}
			let [legend, colour] = work_order_indicator(data);
			return ` <span class="indicator ${colour}">${frappe.utils.get_form_link("Work Order", value, true)}, ${legend}</span> (${data.wo_produced_qty}/${data.wo_qty})`;
		}
		if (col.fieldname === "serial_nos" && data.serial_nos) {
			return `${cartridge_status_link(data.serial_nos)}`;
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
		if (col.fieldname === "open_delivery_notes" && value) {
			let [legend, colour] = delivery_note_indicator(data);
			return ` <span class="indicator ${colour}">${value.split(" ").map(n => frappe.utils.get_form_link("Delivery Note", n, true))}, ${legend}</span> (${data.open_delivery_qty}/${data.remaining_qty})`;
		}
		return default_formatter(value, row, col, data);
	}
};

// Stolen from work_order_list.js on ERPNext 
function work_order_indicator(doc) {
	if (doc.wo_status === "Submitted") {
		return [__("Not Started"), "orange"];
	} else {
		return [__(doc.wo_status), {
			"Draft": "red",
			"Stopped": "red",
			"Not Started": "red",
			"In Process": "orange",
			"Completed": "green",
			"Cancelled": "darkgrey"
		}[doc.wo_status]];
	}
}

function delivery_note_indicator(row) {
	// With the current SQL query, only draft DNs can appear...
	return ["Draft", "red"]
}

function cartridge_status_link(serial_nos) {
	return bnovate.modals.report_link(
		serial_nos,
		'cartStatusModal',
		'Cartridge Status',
		`Cartridge Status for this SO item`,
		{
			serial_no: serial_nos,  // Note that this is encoded in a data- tag, so it'll be a comma-separated string
		});
}