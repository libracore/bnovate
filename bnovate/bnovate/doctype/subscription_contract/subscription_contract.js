// Copyright (c) 2023, bNovate, ITST, libracore and contributors
// For license information, please see license.txt

{% include 'erpnext/selling/sales_common.js' %}

frappe.provide('bnovate.subscription_contract');

frappe.ui.form.on('Subscription Contract', {
	refresh(frm) {
		frm.add_custom_button(__("Create Invoice"), async function () {
			frappe.route_options = {
				"customer": frm.doc.customer,
			};
			await frappe.set_route("query-report", "Aggregate Invoicing");
			frappe.query_report.refresh();
		});
	},
	end_date(frm) {
		// if end date is defined, set it to the end of a period.
		if (frm.doc.end_date) {
			const interval = frm.doc.interval === "Yearly" ? 12 : 1;
			let billing_start = frm.doc.start_date;  // start of next billing period
			let billing_end = frappe.datetime.add_days(billing_start, -1) // end of previous billing period
			while (billing_start <= frm.doc.start_date || billing_end < frm.doc.end_date) {
				billing_start = frappe.datetime.add_months(billing_start, interval);
				billing_end = frappe.datetime.add_days(billing_start, -1)
			}
			if (billing_end != frm.doc.end_date) {
				frappe.msgprint({
					title: __("Info"),
					message: __("End date was changed to the next end of billing cycle"),
					color: "green",
				});
				frm.doc.end_date = billing_end;
				frm.refresh_field('end_date');
			}
		}
	},
	start_date(frm) {
		// TODO move these to controller
		frm.doc.transaction_date = frm.doc.start_date; // Helps SellingController methods work for pricing for example
		frm.trigger('currency');
		frm.trigger('end_date');
	},
	interval(frm) {
		frm.trigger('end_date');
	},
	async before_cancel(frm) {
		// Only allow cancellation if no invoices are open
		const invoices = await frappe.db.get_list("Sales Invoice", { filters: { subscription: frm.doc.name } });
		if (!invoices.length) {
			return;
		}
		await new Promise((resolve, reject) => {
			frappe.confirm("If invoices are already created, do not cancel. Change the subscription End Date instead.<br><br>Do you still want to try?",
				() => { resolve(); },
				() => {
					frappe.validated = false;
					resolve();
				}
			)
		});
	}
});

// frappe.ui.form.on('Subscription Contract Item', {
// 	item_code(frm, cdt, cdn) {
// 		var d = locals[cdt][cdn];
// 		if (d.item_code) {
// 			frappe.call({
// 				'method': "frappe.client.get_list",
// 				'args': {
// 					'doctype': "Item Price",
// 					'filters': [
// 						["item_code", "=", d.item_code],
// 						["selling", "=", 1]
// 					],
// 					'fields': ["price_list_rate"]
// 				},
// 				'callback': function (response) {
// 					if ((response.message) && (response.message.length > 0)) {
// 						frappe.model.set_value(cdt, cdn, "rate", response.message[0].price_list_rate);
// 					}
// 				}
// 			});
// 		}
// 	}
// });


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
// 			'items': ['Subscription Contract'],
// 			'label': 'Subscription',
// 		})
// 		frm.dashboard.data.internal_links['Subscription Contract'] = ['items', 'subscription'];
// 	},
// })

// Subclass SellingController to use their price rate mechanisms
bnovate.subscription_contract.SubscriptionContractController = erpnext.selling.SellingController.extend({
	onload: function (doc, dt, dn) {
		this._super();

		// Override item filters set by SellingController
		this.frm.set_query("item_code", "items", function () {
			return { filters: { enable_deferred_revenue: true } }
		});
		if (!this.frm.doc.start_date) {
			this.frm.set_value('start_date', frappe.datetime.add_days(frappe.datetime.month_end(), 1));
		}
	},
	payment_terms_template() {
		// Do nothing, just override parent class behaviour of rebuilding terms table.
	},
	// override some methods from transaction.js

	_get_args(item) {
		let me = this;
		let answer = this._super();
		answer.transaction_date = me.frm.doc.start_date;
		// console.log(answer);
		return answer
	},
	currency() {
		console.log("Currency called")
		var transaction_date = this.frm.doc.start_date;
		var me = this;
		this.set_dynamic_labels();
		var company_currency = this.get_company_currency();
		// Added `ignore_pricing_rule` to determine if document is loading after mapping from another doc
		if (this.frm.doc.currency && this.frm.doc.currency !== company_currency
			&& !this.frm.doc.ignore_pricing_rule) {

			this.get_exchange_rate(transaction_date, this.frm.doc.currency, company_currency,
				function (exchange_rate) {
					if (exchange_rate != me.frm.doc.conversion_rate) {
						// me.set_margin_amount_based_on_currency(exchange_rate);
						// me.set_actual_charges_based_on_currency(exchange_rate);
						me.frm.set_value("conversion_rate", exchange_rate);
					}
				});
		} else {
			this.conversion_rate();
		}
	},
	apply_price_list(item, reset_plc_conversion) {
		// console.log("called");
		console.log(this._get_args());
		this._super(item, reset_plc_conversion);
	},
	get_exchange_rate(transaction_date, from_currency, to_currency, callback) {
		var args = "for_selling";

		if (!transaction_date || !from_currency || !to_currency) return;
		return frappe.call({
			method: "erpnext.setup.utils.get_exchange_rate",
			args: {
				transaction_date: transaction_date,
				from_currency: from_currency,
				to_currency: to_currency,
				args: args
			},
			callback: function (r) {
				callback(flt(r.message));
			}
		});
	},
})

$.extend(cur_frm.cscript, new bnovate.subscription_contract.SubscriptionContractController({ frm: cur_frm }));
