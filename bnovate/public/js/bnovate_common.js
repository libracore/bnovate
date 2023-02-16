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
