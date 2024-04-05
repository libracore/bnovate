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
    pickup_customer: async (frm) => fill_from_pickup_business(frm),
    pickup_company: async (frm) => fill_from_pickup_business(frm),
    pickup_contact_name: async (frm) => fill_from_pickup_contact(frm),
    pickup_contact_person: async (frm) => fill_from_pickup_contact(frm),

    delivery_customer: async (frm) => fill_from_delivery_business(frm),
    delivery_company: async (frm) => fill_from_delivery_business(frm),
    delivery_contact_name: async (frm) => fill_from_delivery_contact(frm),
    // delivery_contact_person: Field doesn't exist!

    bill_customer: async (frm) => fill_from_bill_business(frm),
    bill_company: async (frm) => fill_from_bill_business(frm),
    bill_contact_name: async (frm) => fill_from_bill_contact(frm),

    async fill_pickup_data(frm) {
        await frm.call('get_invalid_links'); // Force trigger "fetch_from" methods
        fill_from_pickup_business(frm);
        fill_from_pickup_contact(frm);
    },
    async fill_delivery_data(frm) {
        await frm.call('get_invalid_links'); // Force trigger "fetch_from" methods
        fill_from_delivery_business(frm);
        fill_from_delivery_contact(frm);
    },
    async fill_bill_data(frm) {
        await frm.call('get_invalid_links'); // Force trigger "fetch_from" methods
        fill_from_bill_business(frm);
        fill_from_bill_contact(frm);
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

// Fill tax values either from linked Company, Customer, or Supplier
async function fill_from_pickup_business(frm) {
    let values = {
        tax_id: null,
        eori_number: null,
    }

    if (frm.doc.pickup_from_type == "Customer") {
        if (!frm.doc.pickup_customer)
            return;
        values = await frappe.db.get_doc("Customer", frm.doc.pickup_customer);
    } else if (frm.doc.pickup_from_type == "Company") {
        if (!frm.doc.pickup_company)
            return;
        values = await frappe.db.get_doc("Company", frm.doc.pickup_company);
    } else if (frm.doc.pickup_from_type == "Supplier") {
        // Not needed at this time
    }

    frm.set_value('pickup_tax_id', values.tax_id);
    frm.set_value('pickup_eori_number', values.eori_number);
}

// Fill contact information from linked Contact or User
async function fill_from_pickup_contact(frm) {
    // 
    let values = {
        contact_display: null,
        contact_email: null,
        contact_phone: null,
    }

    if (frm.doc.pickup_from_type == "Customer") {
        if (!frm.doc.pickup_contact_name)
            return;
        values = await get_contact_details(frm.doc.pickup_contact_name);
    } else if (frm.doc.pickup_from_type == "Company") {
        if (!frm.doc.pickup_contact_person)
            return;
        values = await get_company_contact_details(frm.doc.pickup_contact_person);
    } else if (frm.doc.pickup_from_type == "Supplier") {
        // Not needed at this time
    }

    frm.set_value('pickup_contact_display', values.contact_display);
    frm.set_value('pickup_contact_email_rw', values.contact_email);
    frm.set_value('pickup_contact_phone', values.contact_phone);
}

/************ DELIVERY ****************/

// Fill tax values either from linked Company, Customer, or Supplier
async function fill_from_delivery_business(frm) {
    let values = {
        tax_id: null,
        eori_number: null,
    }

    if (frm.doc.delivery_to_type == "Customer") {
        if (!frm.doc.delivery_customer)
            return;
        values = await frappe.db.get_doc("Customer", frm.doc.delivery_customer);
    } else if (frm.doc.delivery_to_type == "Company") {
        if (!frm.doc.delivery_company)
            return;
        values = await frappe.db.get_doc("Company", frm.doc.delivery_company);
    } else if (frm.doc.delivery_to_type == "Supplier") {
        // Not needed at this time
    }

    frm.set_value('delivery_tax_id', values.tax_id);
    frm.set_value('delivery_eori_number', values.eori_number);
}

// Fill contact information from linked Contact or User
async function fill_from_delivery_contact(frm) {
    // 
    let values = {
        contact_display: null,
        contact_email: null,
        contact_phone: null,
    }

    if (frm.doc.delivery_to_type == "Customer") {
        if (!frm.doc.delivery_contact_name)
            return;
        values = await get_contact_details(frm.doc.delivery_contact_name);
    } else if (frm.doc.delivery_to_type == "Company") {
        if (!frm.doc.delivery_contact_person)
            return;
        values = await get_company_contact_details(frm.doc.delivery_contact_person);
    } else if (frm.doc.delivery_to_type == "Supplier") {
        // Not needed at this time
    }

    frm.set_value('delivery_contact_display', values.contact_display);
    frm.set_value('delivery_contact_email_rw', values.contact_email);
    frm.set_value('delivery_contact_phone', values.contact_phone);
}

/************ BILL ****************/

// Fill tax values either from linked Company, Customer, or Supplier
async function fill_from_bill_business(frm) {
    let values = {
        tax_id: null,
        eori_number: null,
    }

    if (frm.doc.bill_to_type == "Customer") {
        if (!frm.doc.bill_customer)
            return;
        values = await frappe.db.get_doc("Customer", frm.doc.bill_customer);
    } else if (frm.doc.bill_to_type == "Company") {
        if (!frm.doc.bill_company)
            return;
        values = await frappe.db.get_doc("Company", frm.doc.bill_company);
    } else if (frm.doc.bill_to_type == "Supplier") {
        // Not needed at this time
    }

    frm.set_value('bill_tax_id', values.tax_id);
    frm.set_value('bill_eori_number', values.eori_number);
}

// Fill contact information from linked Contact or User
async function fill_from_bill_contact(frm) {
    // 
    let values = {
        contact_display: null,
        contact_email: null,
        contact_phone: null,
    }

    if (frm.doc.bill_to_type == "Customer") {
        if (!frm.doc.bill_contact_name)
            return;
        values = await get_contact_details(frm.doc.bill_contact_name);
    } else if (frm.doc.bill_to_type == "Company") {
        if (!frm.doc.bill_contact_person)
            return;
        values = await get_company_contact_details(frm.doc.bill_contact_person);
    } else if (frm.doc.bill_to_type == "Supplier") {
        // Not needed at this time
    }

    frm.set_value('bill_contact_display', values.contact_display);
    frm.set_value('bill_contact_email_rw', values.contact_email);
    frm.set_value('bill_contact_phone', values.contact_phone);
}

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
