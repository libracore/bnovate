/*  ***********************
 * This file contains common global functions 
 * 
 *  *********************** */

function get_label(doctype, docname, print_format, label_reference) {
  window.open(
    frappe.urllib.get_full_url(
      "/api/method/bnovate.bnovate.utils.labels.download_label_for_doc"
      + "?doctype=" + encodeURIComponent(doctype)
      + "&docname=" + encodeURIComponent(docname)
      + "&print_format=" + encodeURIComponent(print_format)
      + "&label_reference=" + encodeURIComponent(label_reference)
    ),
    "_blank"
  );
}

/***********************************
 * Client-side wrappers for IoT APIS
 ***********************************/

// Get RMS device id based on device serial number
async function rms_get_id(serial) {
  let resp = await frappe.call({
    method: "bnovate.bnovate.utils.iot_apis.rms_get_id",
    args: {
      serial
    }
  });
  return resp.message;
}

// Get info from single device from RMS id
async function rms_get_device(device_id) {
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
async function rms_get_sessions(device_id) {
  let sessions = await frappe.call({
    method: "bnovate.bnovate.utils.iot_apis.rms_get_access_sessions",
    args: {
      device_id
    }
  });
  return sessions.message;
}

// Open a new session for an existing remote configuration
async function rms_start_session(config_id, device_id) {
  let resp = await frappe.call({
    method: "bnovate.bnovate.utils.iot_apis.rms_start_session",
    args: {
      config_id
    }
  });
  const channel = resp.message;

  while (true) {
    const status = await rms_get_status(channel);
    let [last_update] = status[device_id].slice(-1);

    frappe.show_progress("Starting session....", status[device_id].length, 8, last_update?.value);

    if (last_update.status === "error" || last_update.status === "completed") {
      frappe.hide_progress();

      if (last_update.status === "error") {
        console.log(last_update)
        frappe.msgprint({
          title: __("Error initializing connection"),
          message: last_update.value || last_update.errorCode.toString(),
          indicator: 'red',
        })
      }
      break;
    }

    // Sleep 1 sec and loop again
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
}

// Get RMS device id based on device serial number
async function rms_get_status(channel) {
  let resp = await frappe.call({
    method: "bnovate.bnovate.utils.iot_apis.rms_get_status",
    args: {
      channel
    }
  });
  return resp.message;
}