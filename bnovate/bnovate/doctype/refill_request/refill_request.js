// Copyright (c) 2023, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Refill Request', {
	refresh(frm) {
		if (frm.doc.docstatus == 1) {

			if (frm.doc.shipment) {
				frm.add_custom_button(__('Unlink Shipment'), () => {
					frm.doc.shipment = null;
					frm.save('Update');
				})
			}

			frm.add_custom_button(__('Sales Order'), () => frm.events.make_sales_order(frm), __('Create'))
		}
	},

	make_sales_order(frm) {
		frappe.model.open_mapped_doc({
			method: "bnovate.bnovate.doctype.refill_request.refill_request.make_sales_order",
			frm
		});
	},
});
