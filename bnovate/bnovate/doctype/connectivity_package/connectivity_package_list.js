frappe.require("/assets/bnovate/js/iot.js")  // provides bnovate.iot

frappe.listview_settings['Connectivity Package'] = {
    onload(lv) {
        lv.page.add_inner_button(__("View Map"), () => {
            frappe.set_route("device-map");
        });
    },

    async primary_action() {
        const values = await bnovate.utils.prompt('Create new connectivity package', [{
            label: 'QR code',
            fieldname: 'qr_contents',
            fieldtype: 'Data',
            reqd: false,
        }, {
            label: 'html1',
            fieldname: 'html1',
            fieldtype: 'HTML',
            options: 'Scan the QR code above <b>OR</b> manually fill values below',
        }, {
            label: 'Teltonika Serial No',
            fieldname: 'teltonika_serial',
            fieldtype: 'Link',
            options: 'Serial No',
            reqd: false,
        }, {
            label: 'IMEI',
            fieldname: 'imei',
            fieldtype: 'Data',
            reqd: false,
        }], "Create", "Cancel");

        if (!values) return;

        if (values.qr_contents) {
            frappe.route_options = bnovate.iot.decode_teltonika_qr(values.qr_contents);
        } else {
            frappe.route_options = values;
        }

        frappe.set_route("Form", "Connectivity Package", "New Item");


    }
}