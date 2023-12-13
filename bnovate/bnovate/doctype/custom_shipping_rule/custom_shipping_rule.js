// Copyright (c) 2023, bnovate, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Custom Shipping Rule', {
	refresh: function (frm) {
		frm.trigger('toggle_reqd');
	},
	calculate_based_on: function (frm) {
		frm.trigger('toggle_reqd');
	},
	toggle_reqd: function (frm) {
		frm.toggle_reqd("shipping_amount", frm.doc.calculate_based_on === 'Fixed');
		frm.toggle_reqd("conditions", frm.doc.calculate_based_on !== 'Fixed');
	}
});
