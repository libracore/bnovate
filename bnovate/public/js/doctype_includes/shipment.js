/* Customisations for Shipment
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 * Add DHL integrations
 * 
 */

frappe.ui.form.on("Shipment", {

    refresh(frm) {
        if (cur_frm.doc.docstatus <= 1) {
            frm.add_custom_button(__("Get Estimate"), () => get_price(frm));

            // TODO: only create shipment if status is Submitted, not booked.
            frm.add_custom_button(__("Create Shipment"), () => create_shipment(frm));
        }

        if (get_label_attachments(frm).length > 0) {
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

    // Get contacts in the case of a Customer address
    async pickup_contact_name(frm) {
        if (!frm.doc.pickup_contact_name)
            return;
        const deets = await get_contact_details(frm.doc.pickup_contact_name);
        frm.set_value('pickup_contact_display', deets.contact_display);
        frm.set_value('pickup_contact_email', deets.contact_email);
        frm.set_value('pickup_contact_phone', deets.contact_phone);
    },

    async delivery_contact_name(frm) {
        if (!frm.doc.delivery_contact_name)
            return;
        const deets = await get_contact_details(frm.doc.delivery_contact_name);
        frm.set_value('delivery_contact_display', deets.contact_display);
        frm.set_value('delivery_contact_email', deets.contact_email);
        frm.set_value('delivery_contact_phone', deets.contact_phone);
    },

    // Get contacts in the case of a Company address
    async pickup_contact_person(frm) {
        if (!frm.doc.pickup_contact_person)
            return;

        const deets = await get_company_contact_details(frm.doc.pickup_contact_person);
        frm.set_value('pickup_contact_display', deets.contact_display);
        frm.set_value('pickup_contact_email', deets.contact_email);
        frm.set_value('pickup_contact_phone', deets.contact_phone);
    },

})

function check_dirty(frm) {
    if (frm.is_dirty()) {
        frappe.msgprint('Please save document first');
        return true;
    }
    return false
}

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

    const resp = await frappe.call({
        method: "bnovate.bnovate.utils.shipping.create_shipment",
        args: {
            shipment_docname: frm.doc.name,
        }
    });

    console.log(resp.message);
    frm.reload_doc();
    return resp.message;
}

// Get details based on contact docname
async function get_contact_details(contact) {
    const resp = await frappe.call({
        method: "frappe.contacts.doctype.contact.contact.get_contact_details",
        args: {
            contact
        },
    });

    return resp.message;
}

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
window.get_company_contact_details = get_company_contact_details;

function get_label_attachments(frm) {
    // Return attachments that have "label" in the name
    const attachments = frappe.model.docinfo[frm.doc.doctype][frm.doc.name]?.attachments || [];
    return attachments.filter(row => row.file_name.indexOf('label') >= 0);
}


function print_labels(frm) {
    const attachments = get_label_attachments(frm);
    attachments.forEach(att => bnovate.utils.print_url(att.file_url));
    return;
}