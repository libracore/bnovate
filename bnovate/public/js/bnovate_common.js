// Set navbar to an obvious colour if running on dev machine:
if (window.location.host.indexOf("localhost") >= 0) {
  let link = document.createElement('link');
  link.type = 'text/css';
  link.rel = 'stylesheet';
  link.href = '/assets/bnovate/bnovate-dev.css';
  document.querySelector('head').appendChild(link);
}
if (frappe.datetime.get_today && frappe.datetime.get_today().endsWith('04-01')) {
  console.log("Party time!")
  document.querySelector("body").classList.add('party-time');
}

frappe.provide("bnovate.utils")

bnovate.utils.sleep = function (ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

bnovate.utils.confetti = function () {

  const pick_random_item = function (arr) {
    if (arr.length === 0) {
      return null;
    }
    return arr[Math.floor(Math.random() * arr.length)];

  }

  const configs = [
    {},
    { confettiRadius: 12, confettiNumber: 100 },
    { emojis: ['🌈', '⚡️', '💥', '✨', '💫', '🌸'] },
    { emojis: ['⚡️', '💥', '✨', '💫'] },
    { emojis: ['🦄'], confettiRadius: 100, confettiNumber: 30 },
    {
      confettiColors: ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec', '#3a86ff'],
      confettiRadius: 10,
      confettiNumber: 150,
    },
    {
      confettiColors: ['#9b5de5', '#f15bb5', '#fee440', '#00bbf9', '#00f5d4'],
      confettiRadius: 6,
      confettiNumber: 300,
    },

  ]
  bnovate.utils.confettiPopper = bnovate.utils.confettiPopper || new JSConfetti();
  return bnovate.utils.confettiPopper.addConfetti(pick_random_item(configs));
}


/*  ***********************
 * This file contains common global functions 
 *  *********************** */

function print_url(url) {
  frappe.show_progress("Preparing...", 10, 100);
  setTimeout(() => frappe.show_progress("Preparing...", 60, 100), 500);
  setTimeout(() => frappe.show_progress("Preparing...", 80, 100), 900);
  setTimeout(() => frappe.hide_progress(), 1000);
  let iframe = document.createElement('iframe');
  iframe.style.display = 'none';
  document.body.append(iframe);

  iframe.addEventListener('load', () => {
    setTimeout(() => {
      iframe.focus();
      iframe.contentWindow.print();
      frappe.hide_progress();
      // I cannot find a way get afterprint event working in order to destroy the iframe...
    }, 1);
  });

  iframe.src = url;
}
bnovate.utils.print_url = print_url;

function get_label(doctype, docname, print_format, label_reference) {
  // To print directly, we place content in an iframe and trigger print from there:
  print_url(frappe.urllib.get_full_url(
    "/api/method/bnovate.bnovate.utils.labels.download_label_for_doc"
    + "?doctype=" + encodeURIComponent(doctype)
    + "&docname=" + encodeURIComponent(docname)
    + "&print_format=" + encodeURIComponent(print_format)
    + "&label_reference=" + encodeURIComponent(label_reference)
  ))
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

bnovate.utils.get_random_id = async function () {
  let resp = await frappe.call({
    method: 'bnovate.bnovate.utils.get_random_id',
    args: {
    }
  })
  return resp.message;
}

bnovate.utils.get_naming_series = async function () {
  let resp = await frappe.call({
    method: 'bnovate.bnovate.utils.items.get_naming_series',
  })
  return resp.message;
}

bnovate.utils.set_naming_series = async function (prefix, number) {
  let resp = await frappe.call({
    method: 'bnovate.bnovate.utils.items.set_naming_series',
    args: {
      prefix,
      number
    }
  })
  return resp.message;
}

bnovate.utils.run_report = async function (report_name, filters) {
  let resp = await frappe.call({
    method: "frappe.desk.query_report.run",
    args: {
      report_name,
      filters,
    }
  })
  return resp.message;
}

// Fetch value from settings
bnovate.utils.get_setting = async function (key) {
  return frappe.db.get_single_value("bNovate Settings", key)
}


// Promise-ified frappe prompt:
bnovate.utils.prompt = function (title, fields, primary_action_label, secondary_action_label) {
  return new Promise((resolve, reject) => {
    const d = new frappe.ui.Dialog({
      title,
      fields,
      primary_action_label,
      secondary_action_label,
      primary_action(values) {
        resolve(values);
        this.hide();
      },
      secondary_action() { resolve(null); },
    })
    d.show();
  })
}

bnovate.utils.html_dialog = function (title, body) {
  return new Promise((resolve, reject) => {
    const d = new frappe.ui.Dialog({
      title,
      fields: [{
        fieldname: 'description',
        fieldtype: 'HTML',
        options: body || '',
      }],
      secondary_action() { resolve(null); },
    })
    d.show();
  })
}

// Email dialog that picks all emails from the doc
bnovate.utils.email_dialog = function (frm, template_name) {
  if (frm.is_dirty()) {
    frappe.msgprint('Please save document before emailing');
    return;
  }

  // doc.email was set at refresh, fetching from Shipping address
  var recipients = [frm.doc.email || '', frm.doc.email_id || '', frm.doc.contact_email || ''].filter(i => i).join(', ');
  var cc = "";

  var doc = Object.assign({}, frm.doc);
  doc.carrier = frm.doc.carrier || "";
  doc.tracking_no = frm.doc.tracking_no || "";

  // Render template on the server side:
  let dlg = frappe.show_progress("Rendering email...", 33, 100, "Please wait.");
  frappe.call({
    method: 'frappe.email.doctype.email_template.email_template.get_email_template',
    args: {
      template_name: template_name,
      doc: doc,
    },
    callback: function (r) {
      dlg.hide();
      frm.composer = new frappe.views.CommunicationComposer({
        doc: frm.doc,
        subject: r.message.subject,
        recipients: recipients,
        cc: cc,
        attach_document_print: 1,
        message: r.message.message,
      });
      setTimeout(() => frm.composer.select_attachments(), 1000);
    },
  });
}

bnovate.utils.is_fill = function (item_code) {
  return item_code !== undefined && item_code.startsWith("FIL");
}

bnovate.utils.is_enclosure = function (item_code) {
  return item_code !== undefined && (item_code.startsWith("ENC") || item_code === '100146');
}


/*********************************
 * Code to set enclosure owners
 *********************************/

bnovate.utils.get_history_report = async function () {
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

bnovate.utils.set_cartridge_owners = async function (owners) {
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


