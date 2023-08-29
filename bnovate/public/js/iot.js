frappe.provide("bnovate.iot");


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

// Open a new session for an existing remote configuration
bnovate.iot.rms_start_session = async function rms_start_session(config_id, device_id,
    start_session_method = null,
    get_status_method = null,
) {
    frappe.show_progress(__("Starting session...."), 0, 8, __("Connecting..."));
    let resp = {};

    try {
        resp = await frappe.call({
            method: start_session_method || 'bnovate.bnovate.utils.iot_apis.rms_start_session',
            args: {
                config_id,
            }
        });
    } catch {
        frappe.hide_progress();
    }

    const channel = resp.message;

    while (true) {

        const status = await bnovate.iot.rms_get_status(channel, get_status_method);
        console.log(status);
        // if (!status[device_id]) {
        //     continue;
        // }

        let [last_update] = status[device_id].slice(-1);
        frappe.show_progress(__("Starting session...."), status[device_id].length, 8, last_update ? last_update.value : null);

        if (last_update.status === "error" || last_update.status === "warning" || last_update.status === "completed") {
            frappe.hide_progress();

            if (last_update.status === "error" || last_update.status === "warning") {
                console.log(last_update)
                frappe.msgprint({
                    title: __("Error initializing connection"),
                    message: last_update.value || last_update.errorCode.toString(),
                    indicator: 'red',
                })
                return;
            }

            return last_update.link
        }

        // Sleep 1 sec and loop again
        await new Promise(resolve => setTimeout(resolve, 1000))
    }
}

// Get status updates on notification channel
bnovate.iot.rms_get_status = async function rms_get_status(channel, method = null) {
    let resp = await frappe.call({
        method: method || 'bnovate.bnovate.utils.iot_apis.rms_get_status',
        args: {
            channel
        }
    });
    return resp.message;
}

// Set name and auto-configure remotes
bnovate.iot.rms_initialize_device = async function rms_initialize_device(device_id, device_name) {
    let resp = await frappe.call({
        method: "bnovate.bnovate.utils.iot_apis.rms_initialize_device",
        args: {
            device_id,
            device_name
        }
    });
    return resp.message;
}


// Get status of an instrument, to fetch SN for example
bnovate.iot.get_status = async function get_status(device_id, password, attempt = 1) {
    if (attempt >= 3) {
        return;
    }

    const connections = await bnovate.iot.rms_get_sessions(device_id);
    const https = connections.find(s => s.protocol == "https");

    if (!https) {
        frappe.throw("No HTTPS connections available.");
        return;
    }

    if (!https.sessions.length) {
        await bnovate.iot.rms_start_session(https.id, device_id);
        return bnovate.iot.get_status(device_id, password, attempt + 1)
    }

    const url = 'https://' + https.sessions[0].url + '/api/status';
    const headers = { 'Authorization': 'Basic ' + btoa('guest:' + password) };
    let resp = await fetch(url, { headers });
    let status = await resp.json();
    return status;
}