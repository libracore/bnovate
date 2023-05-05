// Copyright (c) 2023, libracore and contributors
// For license information, please see license.txt

frappe.require("/assets/bnovate/js/storage.js")

frappe.ui.form.on('Storage Location', {
	refresh(frm) {
		frm.add_custom_button("Find", () => bnovate.storage.find_serial_no());
		frm.add_custom_button("Store", () => {
			bnovate.storage.store_serial_no(frm.doc.name);
			frm.reload_doc();
		});
		frm.add_custom_button("Remove", () => bnovate.storage.remove_serial_no());

		if (frm.doc.key) {
			const url = `${location.origin}/internal/storage/${frm.doc.key}`
			frm.fields_dict.url.wrapper.innerHTML = `<a href="${url}">Public Link</a>`
		}
	},

	async set_key(frm) {
		const key = await bnovate.utils.get_random_id();
		frm.set_value("key", key);
		frm.save();
	},
});

