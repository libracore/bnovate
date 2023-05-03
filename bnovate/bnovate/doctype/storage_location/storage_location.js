// Copyright (c) 2023, libracore and contributors
// For license information, please see license.txt

frappe.provide("bnovate.storage");

frappe.ui.form.on('Storage Location', {
	refresh(frm) {
		frm.add_custom_button("Find", () => frm.events.find(frm));
		frm.add_custom_button("Store", () => frm.events.store(frm));
		frm.add_custom_button("Remove", () => frm.events.remove(frm));

		if (frm.doc.key) {
			const url = `/storage/${frm.doc.key}`
			frm.fields_dict.url.wrapper.innerHTML = `<a href="${url}">${url}</a>`
		}
	},

	async set_key(frm) {
		const key = await bnovate.utils.get_random_id();
		frm.set_value("key", key);
		frm.save();
	},

	async find(frm) {
		const serial_no = await prompt_sn("Find");
		if (serial_no) {
			const location = await bnovate.storage.find_serial_no(serial_no.serial_no);
			frappe.msgprint(`<b>Location:</b> ${location.title}<br><b>Slot:</b> ${location.slot}`, `Item found`);
		}
	},

	async store(frm) {
		const serial_no = await prompt_sn("Store");
		if (serial_no) {
			const location = await bnovate.storage.store_serial_no(frm.doc.name, serial_no.serial_no);
			frm.reload_doc();
			frappe.msgprint(`<b>Location:</b> ${location.title}<br><b>Slot:</b> ${location.slot}`, `Item stored in`);
		}
	},

	async remove(frm) {
		const serial_no = await prompt_sn("Remove");
		if (serial_no) {
			const location = await bnovate.storage.remove_serial_no(serial_no.serial_no);
			frm.reload_doc();
			frappe.msgprint(`<b>Location:</b> ${location.title}<br><b>Slot:</b> ${location.slot}`, `Item removed from storage`);
		}
	}
});


bnovate.storage.find_serial_no = async function find_serial_no(serial_no) {
	const resp = await frappe.call({
		method: "bnovate.bnovate.doctype.storage_location.storage_location.find_serial_no",
		args: {
			serial_no
		}
	})
	return resp.message;
}

bnovate.storage.store_serial_no = async function store_serial_no(location_name, serial_no) {
	const resp = await frappe.call({
		method: "bnovate.bnovate.doctype.storage_location.storage_location.store_serial_no",
		args: {
			location_name,
			serial_no
		}
	})
	return resp.message;
}

bnovate.storage.remove_serial_no = async function remove_serial_no(serial_no) {
	const resp = await frappe.call({
		method: "bnovate.bnovate.doctype.storage_location.storage_location.remove_serial_no",
		args: {
			serial_no
		}
	})
	return resp.message;
}

// Helpers
// Promise-ified frappe prompt:
function prompt_sn(primary_action_label) {
	return new Promise((resolve, reject) => {
		const d = new frappe.ui.Dialog({
			title: "Scan Serial No",
			fields: [{
				label: "Serial No",
				fieldname: "serial_no",
				fieldtype: "Data",
				reqd: 1,
			}],
			primary_action_label,
			secondary_action_label: null,
			primary_action(values) {
				resolve(values);
				this.hide();
			},
			secondary_action() { resolve(null); },
		})
		d.show();
	})
}

