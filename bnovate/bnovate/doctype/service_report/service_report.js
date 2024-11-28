// Copyright (c) 2023, bnovate, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service Report', {
	onload(frm) {

		// Setup queries
		frappe.dynamic_link = { doc: frm.doc, fieldname: 'customer', doctype: 'Customer' }
		frm.set_query('contact_person', erpnext.queries.contact_query);
		frm.set_query("quotation", function () {
			return {
				filters: {
					party_name: frm.doc.customer,
				}
			}
		});
		frm.set_query("subscription_contract", function () {
			return {
				filters: {
					customer: frm.doc.customer,
					status: "Active",
					serial_no: frm.doc.serial_no,
				}
			}
		});
		frm.set_query("quotation", function () {
			return {
				filters: {
					party_name: frm.doc.customer,
				}
			}
		});
		frm.set_query("serial_no", function () {
			return {
				filters: {
					item_group: "Instruments",
					owned_by: frm.doc.customer,
				}
			}
		});
		frm.set_query("set_warehouse", function () {
			return {
				filters: {
					for_user: frm.doc.bnovate_technician,
				}
			}
		});

		frm.set_query("item_code", "items", function () {
			return {
				query: "bnovate.bnovate.doctype.service_report.service_report.item_query",
				filters: {
					warehouse: frm.doc.set_warehouse,
				}
			}
		});
	},

	refresh(frm) {
		if (frm.doc.docstatus == 1) {

			frm.add_custom_button(__("Sales Order"), () => {
				frappe.model.open_mapped_doc({
					method: "bnovate.bnovate.doctype.service_report.service_report.make_sales_order",
					frm: cur_frm
				});
			}, __("Create"));

		}
	}

});
