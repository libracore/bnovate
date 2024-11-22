frappe.require("/assets/bnovate/js/realtime.js");

frappe.provide("bnovate.iot");

/***********************************
 * Utils
 ***********************************/

// Return SN, MAC, IMEI, batch based on the QR code on side of box
bnovate.iot.decode_teltonika_qr = function (contents) {
    // Structure of the string in the QR code:
    // SN:0123456789;I:123456789123456;M:123456789012;B:012;

    const map = { SN: 'teltonika_serial', I: 'imei', M: 'mac_address', B: 'batch' };

    result = {};
    contents
        .split(';')
        .filter(i => !!i)
        .forEach(pair => {
            let [key, value] = pair.split(':')
            if (map[key] !== undefined) {
                result[map[key]] = value;
            }
        })

    return result

}

/***********************************
 * Client-side wrappers for IoT APIS
 ***********************************/

// Get RMS device id based on device serial number
bnovate.iot.rms_get_id = async function rms_get_id(serial) {
    let resp = await frappe.call({
        method: "bnovate.bnovate.utils.iot_apis.rms_get_id",
        args: {
            serial
        }
    });
    return resp.message;
}

// Get info from single device from RMS id
bnovate.iot.rms_get_device = async function rms_get_device(device_id) {
    let resp = await frappe.call({
        method: "bnovate.bnovate.utils.iot_apis.rms_get_device",
        args: {
            device_id
        }
    });
    return resp.message;
}


// Return array of connection configs with active sessions
// Optional device_id. If unspecified, returns all configs.
bnovate.iot.rms_get_sessions = async function rms_get_sessions(device_id) {
    let sessions = await frappe.call({
        method: "bnovate.bnovate.utils.iot_apis.rms_get_access_sessions",
        args: {
            device_id
        }
    });
    return sessions.message;
}

bnovate.iot.sweep_instrument_status = async function (cp_docnames) {
    const resp = await bnovate.realtime.call({
        method: "bnovate.bnovate.doctype.connectivity_package.connectivity_package.sweep_instrument_status",
        args: {
            docnames: cp_docnames
        },
        callback(status) {
            console.log(status)
        }
    })
    frappe.hide_progress();
    return resp.message;
}

bnovate.iot.portal_get_instrument_status = async function (cp_docname) {
    frappe.show_progress(__("Starting session...."), 5, 100);
    try {
        const resp = await bnovate.realtime.call({
            method: "bnovate.www.instruments.portal_get_instrument_status",
            args: {
                cp_docname
            },
            callback(status) {
                if (status.data.progress < 100) {
                    frappe.show_progress(__("Starting session...."), status.data.progress, 100);
                }
            }
        })
        frappe.hide_progress();
        return resp.message;
    } catch (e) {
        frappe.hide_progress();
        throw (e)
    }
}

bnovate.iot.portal_sweep_instrument_status = async function (cp_docnames, callback = (status) => null) {
    const resp = await bnovate.realtime.call({
        method: "bnovate.www.instruments.portal_sweep_instrument_status",
        args: {
            cp_docnames
        },
        callback
    })
    frappe.hide_progress();
    return resp.message;
}

// Start a remote connection session and open in new tab. Authenticates portal users.
bnovate.iot.portal_start_session = async function (config_id, cp_docname) {
    try {
        frappe.show_progress(__("Starting session...."), 0, 100);
        const resp = await bnovate.realtime.call({
            method: "bnovate.www.instruments.portal_start_session",
            args: {
                config_id,
                cp_docname
            },
            callback(status) {
                if (status.data.progress < 100) {
                    frappe.show_progress(__("Starting session...."), status.data.progress, 100);
                }
            },
        })
        const link = resp.message;
        if (link) {
            window.open("https://" + link, "_blank");
        }
        frappe.hide_progress();
    } catch (e) {
        frappe.hide_progress();
        throw (e);
    }
}