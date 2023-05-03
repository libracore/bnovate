// Set navbar to an obvious colour if running on dev machine:
if (window.location.host.indexOf("localhost") >= 0) {
  let link = document.createElement('link');
  link.type = 'text/css';
  link.rel = 'stylesheet';
  link.href = '/assets/bnovate/bnovate-dev.css';
  document.querySelector('head').appendChild(link);
}
if (parseInt(Math.random() * 100) == 42 || frappe.datetime.get_today().endsWith('04-01')) {
  console.log("Party time!")
  document.querySelector("body").classList.add('party-time');
}

frappe.provide("bnovate.utils")


/*  ***********************
 * This file contains common global functions 
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
bnovate.utils.get_label = get_label; // already used in many custom scripts, keep in global namespace.

bnovate.utils.get_next_item_code = async function (prefix) {
  let resp = await frappe.call({
    method: 'bnovate.bnovate.utils.items.get_next_item_code',
    args: {
      prefix
    }
  })
  return resp.message;
}

bnovate.utils.get_random_id = async function get_random_id() {
  let resp = await frappe.call({
    method: 'bnovate.bnovate.utils.get_random_id',
    args: {
    }
  })
  return resp.message;
}

/*********************************
 * Code to set enclosure owners
 *********************************/

// TODO: migrate to own namespace.

async function get_history_report() {
  let resp = await frappe.call({
    method: "frappe.desk.query_report.run",
    args: {
      report_name: "Shipping and Billing History",
      filters: {
      }
    }
  })
  return resp.message;
}

async function get_cartridge_owners() {
  const message = await get_history_report();
  const data = message.result.filter(row => row.customer != "CR-00110");

  let out = [];
  let known_sns = new Set();
  for (let row of data) {

    sns = row.serial_no.trim().toUpperCase().split("\n").map(s => s.trim());

    for (let sn of sns) {
      if (known_sns.has(sn) || sn.startsWith("BNO")) {
        continue;
      }
      if (!(row.shipped_item_code.startsWith("ENC-") || row.shipped_item_code == "100146")) {
        continue;
      }
      known_sns.add(sn);
      out.push({
        serial_no: sn,
        customer: row.customer,
        customer_name: row.customer_name,
        doc: row.delivery_note,
        data: row.ship_date
      })
    }

  }
  return out;
}

async function set_cartridge_owners(owners) {
  // owners as returned by get_cartridge_owners
  let i = 0;
  for (let row of owners) {
    console.log(row.serial_no, i++, owners.length)
    await frappe.db.set_value('Serial No', row.serial_no, {
      owned_by: row.customer,
      owned_by_name: row.customer_name,
      owner_set_by: row.doc,
    })
  }
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

    frappe.show_progress("Starting session....", status[device_id].length, 8, last_update ? last_update.value : null);

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

      return last_update.link
    }

    // Sleep 1 sec and loop again
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
}

// Get status updates on notification channel
async function rms_get_status(channel) {
  let resp = await frappe.call({
    method: "bnovate.bnovate.utils.iot_apis.rms_get_status",
    args: {
      channel
    }
  });
  return resp.message;
}

// TMP
async function rms_initialize_device(device_id, device_name) {
  let resp = await frappe.call({
    method: "bnovate.bnovate.utils.iot_apis.rms_initialize_device",
    args: {
      device_id,
      device_name
    }
  });
  return resp.message;
}


// For fun
async function get_status(device_id, password, attempt = 1) {
  if (attempt >= 3) {
    return;
  }

  const connections = await rms_get_sessions(device_id);
  const https = connections.find(s => s.protocol == "https");

  if (!https) {
    console.log("fail");
    return;
  }

  if (!https.sessions.length) {
    await rms_start_session(https.id, device_id);
    return get_status(device_id, password, attempt + 1)
  }

  // console.log(https)
  const url = 'https://' + https.sessions[0].url + '/api/status';
  const headers = { 'Authorization': 'Basic ' + btoa('user:' + password) };
  // console.log(url, headers);
  let resp = await fetch(url, { headers });
  let status = await resp.json();
  console.log(status);
  return status;
}