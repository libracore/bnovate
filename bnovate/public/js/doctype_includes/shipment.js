/* Customisations for Shipment
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 * Add DHL integrations
 * 
 */

frappe.require("/assets/bnovate/js/realtime.js")

frappe.ui.form.on("Shipment", {

    refresh(frm) {
        if (cur_frm.doc.docstatus <= 1) {
            frm.add_custom_button(__("Get Estimate"), () => get_price(frm));

            // TODO: only create shipment if status is Submitted, not booked.
            frm.add_custom_button(__("Create Shipment"), () => create_shipment(frm));
        }

        if (frm.doc.shipping_label) {
            frm.add_custom_button(__('<i class="fa fa-print"></i> Labels'), () => print_labels(frm));
        }


        // CLICKABLE URLS
        if (frm.doc.tracking_url) {
            $(frm.fields_dict.tracking_url_html.wrapper).html(
                `<div class="form-group">
                    <div class="clearfix"><label class="control-label" style="padding-right: 0px;">${__("Tracking URL")}</label></div>
                    <div class="control-value"><a href="${frm.doc.tracking_url}">${frm.doc.tracking_url}</a></div>
                </div>`
            );
        } else {
            $(frm.fields_dict.tracking_url_html.wrapper).html("");
        }

        if (frm.doc.cancel_pickup_url) {
            $(frm.fields_dict.cancel_pickup_url_html.wrapper).html(
                `<div class="form-group">
                    <div class="clearfix"><label class="control-label" style="padding-right: 0px;">${__("Cancel pickup URL")}</label></div>
                    <div class="control-value"><a href="${frm.doc.cancel_pickup_url}">${frm.doc.cancel_pickup_url}</a></div>
                </div>`
            );
        } else {
            $(frm.fields_dict.cancel_pickup_url_html.wrapper).html("");
        }

    },

    before_submit(frm) {
        if (!(frm.doc.shipment_parcel?.length)) {
            frappe.msgprint(__("Please specify parcels."));
        }
    },

    /* Autofills depend on linked doctypes: Company, Customer, or Supplier */
    async fill_pickup_data(frm) {
        await fill_address(frm, 'pickup');
    },
    async fill_delivery_data(frm) {
        await fill_address(frm, 'delivery');
    },
    async fill_bill_data(frm) {
        await fill_address(frm, 'bill');
    },
})

/**********************************************
 *  FORM COMPLETION HELPERS
 *********************************************/

function check_dirty(frm) {
    if (frm.is_dirty()) {
        frappe.msgprint('Please save document first');
        return true;
    }
    return false
}

// Get contact details based on **contact** docname
async function get_contact_details(contact) {
    const resp = await frappe.call({
        method: "frappe.contacts.doctype.contact.contact.get_contact_details",
        args: {
            contact
        },
    });

    return resp.message;
}

// Get contact details based on **username**
async function get_company_contact_details(user) {
    const resp = await frappe.call({
        method: "erpnext.stock.doctype.shipment.shipment.get_company_contact",
        args: {
            user
        },
    });

    const contact = resp.message;
    return {
        contact_display: [contact.first_name, contact.last_name].join(' ').trim(),
        contact_email: contact.email,
        contact_phone: contact.phone,
    }
}


/************ PICKUP ****************/

async function fill_address(frm, address_type) {

    if (['pickup', 'delivery', 'bill'].indexOf(address_type) < 0) {
        frappe.throw("address_type must be one of: ['pickup', 'delivery', 'bill']")
    }

    const args = {
        address_type,
        address_name: frm.doc[address_type + '_address_name'],
    };
    // business type field is the only one that isn't consistently named...!
    // it can be pickup_from_type, delivery_to_type, or bill_to_type
    const business_type = frm.doc[address_type + '_from_type'] || frm.doc[address_type + '_to_type'];

    if (business_type === 'Company') {
        args.company = frm.doc[address_type + '_company'];
        args.contact = frm.doc[address_type + '_person'];
    } else if (business_type === 'Customer') {
        args.customer = frm.doc[address_type + '_customer'];
        args.contact = frm.doc[address_type + '_contact_name'];
    } else if (business_type === 'Supplier') {
        args.company = frm.doc[address_type + '_supplier'];
    }

    console.log(args)

    const resp = await frappe.call({
        method: 'bnovate.bnovate.utils.shipping.fill_address_data',
        args
    })
    const fields = resp.message;

    Object.entries(fields).forEach(([k, v]) => frm.set_value(k, v));
};
window.fill_address = fill_address;

/************ LABELS ****************/

function get_label_attachments(frm) {
    // Return attachments that have "label" in the name
    const attachments = frappe.model.docinfo[frm.doc.doctype][frm.doc.name]?.attachments || [];
    return attachments.filter(row => row.file_name.indexOf('label') >= 0);
}

function print_labels(frm) {
    // const attachments = get_label_attachments(frm);
    // attachments.forEach(att => bnovate.utils.print_url(att.file_url));
    bnovate.utils.print_url(frm.doc.shipping_label);
}

/**********************************************
 *  API FUNCTIONS
 *********************************************/

async function get_price(frm) {

    if (check_dirty(frm))
        return;

    const resp = await frappe.call({
        method: "bnovate.bnovate.utils.shipping.get_price",
        args: {
            shipment_docname: frm.doc.name,
        }
    });

    const estimatedPickup = frappe.datetime.get_datetime_as_string(resp.message.pickupCapabilities?.localCutoffDateAndTime);
    const estimatedDelivery = frappe.datetime.str_to_user(resp.message.deliveryCapabilities?.estimatedDeliveryDateAndTime);
    const priceEstimate = resp.message.totalPrice?.[0].price;
    const currency = resp.message.totalPrice?.[0].priceCurrency;

    frappe.msgprint(`<b>Pickup until</b>: ${estimatedPickup}<br><b>Delivery estimated on</b>: ${estimatedDelivery}<br><b>Cost estimate</b>: ${priceEstimate} ${currency}`);
    return resp.message;
}

async function create_shipment(frm) {

    if (check_dirty(frm))
        return;

    const resp = await bnovate.realtime.call({
        method: "bnovate.bnovate.utils.shipping.create_shipment",
        args: {
            shipment_docname: frm.doc.name,
        },
        callback(status) {
            console.log(status);
            if (status.data.progress < 100) {
                frappe.show_progress(__("Creating shipment..."), status.data.progress, 100, __(status.data.message));
            }
            if (status.code == 0) {
                frappe.hide_progress();
            }
        }
    });

    console.log(resp.message);
    frm.reload_doc();
    return resp.message;
}
