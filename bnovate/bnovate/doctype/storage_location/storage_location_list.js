{% include "bnovate/bnovate/doctype/storage_location/storage_location.js" %}

frappe.listview_settings['Storage Location'] = {
    onload(lv) {
        lv.page.add_inner_button(__("Find Item"), () => { lv.settings.find() });
    },
    async find() {
        const serial_no = await prompt_sn("Find");
        if (serial_no) {
            const location = await bnovate.storage.find_serial_no(serial_no.serial_no);
            frappe.msgprint(
                `<b>Location:</b> ${frappe.utils.get_form_link("Storage Location", location.location, true, location.title)}<br>
                    <b>Slot:</b> ${location.slot}`,
                `Item found`);
        }
    },
}