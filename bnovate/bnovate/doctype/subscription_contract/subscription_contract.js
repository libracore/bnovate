// Copyright (c) 2023, bNovate, ITST, libracore and contributors
// For license information, please see license.txt

{% include 'erpnext/selling/sales_common.js' %}

frappe.provide('bnovate.subscription_contract');

frappe.ui.form.on('Subscription Contract', {
	async before_cancel(frm) {
		// Only allow cancellation if no invoices are open
		// Cancelling is blocked by the backend anyway, but I want a more helpful message for users.
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
	refresh() {
		this.frm.add_custom_button(__('Modify / Upgrade'), async () => {
			// TODO: restrict permissions to Sales Managers (or whoever can modify SINVs)
			const div = document.createElement('div');
			div.setAttribute('class', 'row form-section');
			div.appendChild(document.createTextNode("Hello world"));
			document.querySelector('.form-page').prepend(div);

			let end_date = await prompt_end_date(this._get_next_billing_end(this.frm.doc.end_date));
			this.end_contract(end_date);
			return;

			await frappe.model.open_mapped_doc({
				method: 'bnovate.bnovate.doctype.subscription_contract.subscription_contract.make_from_self',
				frm: this.frm
			});
		})

		this.frm.add_custom_button(__("Create Invoice"), async () => {
			frappe.route_options = {
				"customer": this.frm.doc.customer,
			};
			await frappe.set_route("query-report", "Aggregate Invoicing");
			frappe.query_report.refresh();
		});
	},
	start_date() {
		this.frm.doc.transaction_date = this.frm.doc.start_date; // Helps SellingController methods work for pricing for example
		this.frm.trigger('currency');
		this.frm.trigger('end_date');
		this.frm.trigger('planned_end_date');
	},
	interval() {
		this.frm.trigger('end_date');
		this.frm.trigger('planned_end_date');
	},
	planned_end_date() {
		console.log("trigged")
		if (this.frm.doc.planned_end_date) {
			const billing_end = this._get_next_billing_end(this.frm.doc.planned_end_date || frappe.datetime.get_today());
			if (billing_end != this.frm.doc.planned_end_date) {
				frappe.msgprint({
					title: __("Info"),
					message: __("Planned End Date was changed to the next end of billing cycle"),
					color: "green",
				});
				// Change value without re-triggering change watcher
				this.frm.doc.planned_end_date = billing_end;
				this.frm.refresh_field('planned_end_date');
			}
		}
	},
	// TODO: allow any end date, but we may need to simplify credit notes
	end_date() {
		// if end date is defined, set it to the end of a period.
		if (this.frm.doc.end_date) {
			const billing_end = this._get_next_billing_end(this.frm.doc.end_date);
			if (billing_end != this.frm.doc.end_date) {
				frappe.msgprint({
					title: __("Info"),
					message: __("End Date was changed to the next end of billing cycle"),
					color: "green",
				});
				this.frm.doc.end_date = billing_end;
				this.frm.refresh_field('end_date');
			}
		}
	},
	_get_next_billing_end(current_end_date) {
		const interval = this.frm.doc.interval === "Yearly" ? 12 : 1;
		let billing_start = this.frm.doc.start_date;  // start of next billing period
		let billing_end = frappe.datetime.add_days(billing_start, -1) // end of previous billing period
		while (billing_start <= this.frm.doc.start_date || billing_end < current_end_date) {
			billing_start = frappe.datetime.add_months(billing_start, interval);
			billing_end = frappe.datetime.add_days(billing_start, -1)
		}
		return billing_end;
	},

	// Modification workflow
	// - Confirm end date of current SC
	// - Set status to show contract is over?
	// - If applicable, find last invoice and adjust service end date
	// - If applicable, issue corresponding credit note
	// - Duplicate SC, starting from day after end date.
	//   - Show on print format that it replaces previous SC.
	async end_contract(end_date) {
		await frappe.call({
			method: 'bnovate.bnovate.doctype.subscription_contract.subscription_contract.close',
			args: {
				docname: this.frm.doc.name,
				end_date: end_date,
			}
		})
		this.frm.reload_doc();
	},

	// override some methods from transaction.js

	_get_args(item) {
		let answer = this._super();
		answer.transaction_date = this.frm.doc.start_date;
		return answer
	},
	payment_terms_template() {
		// Do nothing, just override parent class behaviour of rebuilding terms table.
	},
	currency() {
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


/***************************
 * HELPERS
 ***************************/

function prompt_end_date(default_date) {
	return new Promise((resolve, reject) => {
		let d = new frappe.ui.Dialog({
			title: "Confirm end date of current Subscription",
			fields: [{
				label: "Actual End Date",
				fieldname: "end_date",
				fieldtype: "Date",
				default: default_date,
			}],
			primary_action_label: 'End Contract',
			primary_action(values) {
				resolve(values.end_date);
				d.hide();
			},
			secondary_action() {
				reject();
			}
		});
		d.show();
	})
}