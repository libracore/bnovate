// Copyright (c) 2023, bNovate, ITST, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Subscription Service', {
	onload(frm) {
		frm.set_query("item", "items", function () {
			return { filters: { enable_deferred_revenue: true } }
		});

		if (!frm.doc.start_date) {
			frm.doc.start_date = frappe.datetime.add_days(frappe.datetime.month_end(), 1);
		}
	},
	refresh(frm) {
		frm.add_custom_button(__("Create Invoice"), async function () {
			frappe.route_options = {
				"customer": frm.doc.customer,
			};
			await frappe.set_route("query-report", "Aggregate Invoicing");
			frappe.query_report.refresh();
		});
	},
	before_cancel(frm) {
		frappe.msgprint({
			title: __("Noooo"),
			message: __("Please don't cancel me"),
			indicator: "red",
		});
		frappe.validated = false;
	}
});

frappe.ui.form.on('Subscription Service Item', {
	item(frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (d.item) {
			frappe.call({
				'method': "frappe.client.get_list",
				'args': {
					'doctype': "Item Price",
					'filters': [
						["item_code", "=", d.item],
						["selling", "=", 1]
					],
					'fields': ["price_list_rate"]
				},
				'callback': function (response) {
					if ((response.message) && (response.message.length > 0)) {
						frappe.model.set_value(cdt, cdn, "rate", response.message[0].price_list_rate);
					}
				}
			});
		}
	}
});


// Example of how to draw a report inside a form.
// Assumes field "report" exists of type HTML.
async function draw_report(frm) {
	const resp = await frappe.call({
		method: "frappe.desk.query_report.run",
		args: {
			report_name: "Subscription Invoices",
			filters: {
				subscription: frm.doc.name,
			}
		}
	})
	const report_data = resp.message;
	// if (!report_data.result.length) {
	// 	return;
	// }
	let report = new frappe.views.QueryReport({
		parent: frm.fields_dict.report.wrapper,
		report_name: "Subscription Invoices"
	});
	await report.get_report_doc();
	await report.get_report_settings();
	report.$report = [frm.fields_dict.report.wrapper];
	report.prepare_report_data(report_data);
	report.render_datatable()
}

// Add to custom scripts on Sales Invoice for example, to show links on dashboard:
// Needs to be included in hooks.py (doctype_js)
// frappe.ui.form.on("Sales Invoice", {
// 	before_load(frm) {
// 		frm.dashboard.add_transactions({
// 			'items': ['Subscription Service'],
// 			'label': 'Subscription',
// 		})
// 		frm.dashboard.data.internal_links['Subscription Service'] = ['items', 'subscription'];
// 	},
// })