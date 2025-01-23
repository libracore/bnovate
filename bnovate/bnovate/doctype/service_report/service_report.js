// Copyright (c) 2023, bnovate, libracore and contributors
// For license information, please see license.txt

const CHANNEL_DIRECT = 'Direct';
const CHANNEL_PARTNER = 'Service Partner';
const BILLING_PARTNER = 'Through Service Partner';

frappe.ui.form.on('Service Report', {
	onload(frm) {

		// Setup queries

		// contact_query from erpnext uses frappe.dynamic_link to set filters...
		// frappe.dynamic_link = { doc: frm.doc, fieldname: 'customer', doctype: 'Customer' }
		// frm.set_query('contact_person', erpnext.queries.contact_query);
		frm.set_query('contact_person', function () {
			return {
				// contact_query from frappe package is more flexible than the one from erpnext
				query: 'frappe.contacts.doctype.contact.contact.contact_query',
				filters: {
					link_doctype: 'Customer',
					link_name: frm.doc.customer,
				}
			}
		});

		frm.set_query('service_partner', function () {
			return {
				filters: {
					is_service_partner: 1,
				}
			}
		});

		frm.set_query('technician', function () {
			return {
				query: 'frappe.contacts.doctype.contact.contact.contact_query',
				filters: {
					link_doctype: 'Customer',
					link_name: frm.doc.service_partner,
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
		if (frm.doc.docstatus == 1 && frm.doc.billing_basis !== BILLING_PARTNER && frm.doc.so_docstatus !== 1) {

			frm.add_custom_button(__("Sales Order"), () => {
				frappe.model.open_mapped_doc({
					method: "bnovate.bnovate.doctype.service_report.service_report.make_sales_order",
					frm: cur_frm,
				});
			}, __("Create"));

		}
	},

	channel(frm) {
		frm.toggle_reqd('bnovate_technician', frm.doc.channel === CHANNEL_DIRECT);
		frm.toggle_reqd('service_partner', frm.doc.channel === CHANNEL_PARTNER);
		if (frm.doc.channel == 'Service Partner') {
			frm.set_value('billing_basis', BILLING_PARTNER);
		} else {
			frm.set_value('billing_basis', null);
		}
	},

	async bnovate_technician(frm) {
		console.log(frm.doc)
		const resp = await frappe.db.get_value("Warehouse", { for_user: frm.doc.bnovate_technician }, 'name');
		frm.set_value('set_warehouse', resp.message?.name);
	},

	async technician(frm) {
		let technician_display = null;
		if (frm.doc.technician) {
			technician_display = await bnovate.utils.get_contact_display(frm.doc.technician);
		}
		frm.set_value('technician_name', technician_display);
	},

	reason_for_visit(frm) {
		frm.toggle_reqd('description', frm.doc.reason_for_visit === 'Service');
		frm.toggle_reqd('resolution', frm.doc.reason_for_visit === 'Service');
	},

});
