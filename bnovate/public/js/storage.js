frappe.provide("bnovate.storage");

bnovate.storage.find_serial_no = async function find_serial_no(serial_no, key) {
    if (!serial_no) {
        const input = await bnovate.storage.prompt_sn("Find");
        serial_no = input?.serial_no;
    }

    if (serial_no) {
        const resp = await frappe.call({
            method: "bnovate.bnovate.doctype.storage_location.storage_location.find_serial_no",
            args: {
                serial_no,
                key
            }
        })
        const location = resp.message;
        await bnovate.storage.msgprint(`<b>Location:</b> ${location.title}<br><b>Slot:</b> ${location.slot}`, `Item found`);
        return location
    }
}

bnovate.storage.store_serial_no = async function store_serial_no(location_name, serial_no, key) {
    if (!serial_no) {
        const input = await bnovate.storage.prompt_sn("Store");
        serial_no = input?.serial_no;
    }
    if (serial_no) {

        const resp = await frappe.call({
            method: "bnovate.bnovate.doctype.storage_location.storage_location.store_serial_no",
            args: {
                location_name,
                serial_no,
                key
            }
        })
        const location = resp.message;
        if (cur_frm) {
            cur_frm.reload_doc();
        }
        await bnovate.storage.msgprint(`<b>Location:</b> ${location.title}<br><b>Slot:</b> ${location.slot}`, `Item stored in`);
        return location;
    }
}

bnovate.storage.remove_serial_no = async function remove_serial_no(serial_no, throwErr = true, key = null, discreet = false) {
    if (!serial_no) {
        const input = await bnovate.storage.prompt_sn("Remove");
        serial_no = input?.serial_no;
    }

    if (serial_no) {
        const resp = await frappe.call({
            method: "bnovate.bnovate.doctype.storage_location.storage_location.remove_serial_no",
            args: {
                serial_no,
                "throw": throwErr,
                key,
            }
        })
        const location = resp.message;
        if (cur_frm) {
            cur_frm.reload_doc();
        }
        if (location.title) {
            if (discreet) {
                frappe.show_alert(`Cartridge removed from storage (${location.title} ${location.slot}).`);
            } else {
                await bnovate.storage.msgprint(`<b>Location:</b> ${location.title}<br><b>Slot:</b> ${location.slot}`, `Item removed from storage`);
            }
        }
        return location;
    }
}

// Helpers
// Promise-ified frappe prompt:
bnovate.storage.prompt_sn = function prompt_sn(primary_action_label) {
    return new Promise((resolve, reject) => {
        const d = new frappe.ui.Dialog({
            title: "Enter Serial No",
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

// Simply an await-able dialog
bnovate.storage.msgprint = function msgprint(message, title) {
    return new Promise((resolve, reject) => {
        let dialog = frappe.msgprint(message, title);
        dialog.onhide = () => { resolve() };
        return dialog;
    })
}


bnovate.storage.decode_qr = function decode_qr(qr_string) {
    if (qr_string.trim().startsWith("{")) {
        const qrdata = JSON.parse(qr_string);
        console.log(qrdata);

        return qrdata.enclosure_serial;
    }

    return qr_string;
}