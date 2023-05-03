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

/*********************************
 * Code to set enclosure owners
 *********************************/

// TODO: migrate to own namespace.

bnovate.utils.get_history_report = async function get_history_report() {
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

bnovate.utils.get_cartridge_owners = async function get_cartridge_owners() {
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

bnovate.utils.set_cartridge_owners = async function set_cartridge_owners(owners) {
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


