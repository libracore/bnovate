// Copyright (c) 2023, bNovate, ITST, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Subscription Service', {
	refresh(frm) {
		frm.add_custom_button(__("Create Invoice"), function () {
			frappe.route_options = {};
			frappe.set_route("query-report", "Subscriptions Billable");
		});

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