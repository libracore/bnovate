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
        if (frm.doc.docstatus <= 1) {
            frm.add_custom_button(__("Get Estimate"), () => get_price(frm));

        }

        if (frm.doc.docstatus == 1) {
            if (frm.doc.status == "Submitted") {
                frm.add_custom_button(__("Create Shipment NO Pickup"), () => create_shipment(frm, false));
                frm.add_custom_button(__("Create Shipment AND Pickup"), () => create_shipment(frm, true));
            }

            if (frm.doc.status == "Registered") {
                frm.add_custom_button(__("Request Pickup"), () => request_pickup(frm));

            }

            if (frm.doc.items.findIndex(i => i.refill_request) >= 0) {
                frm.add_custom_button(__("Copy to RR"), () => copy_to_rr(frm));
            }

            if (frm.doc.status == "Completed") {
                if (frm.doc.items.findIndex(i => i.delivery_note) >= 0) {
                    frm.add_custom_button(__("Finalize DN"), () => finalize_dn(frm));
                }
                frm.add_custom_button(__("Cancel Pickup"), () => cancel_pickup(frm));
                frm.add_custom_button(__("Update Tracking"), () => update_tracking(frm));
            }
        }

        if (frm.doc.shipping_label) {
            frm.add_custom_button('<i class="fa fa-print"></i> ' + __('Labels'), () => print_labels(frm));
        }


        // CLICKABLE URLS
        // if (frm.doc.tracking_url) {
        //     $(frm.fields_dict.tracking_url_html.wrapper).html(
        //         `<div class="form-group">
        //             <div class="clearfix"><label class="control-label" style="padding-right: 0px;">${__("Tracking URL")}</label></div>
        //             <div class="control-value"><a href="${frm.doc.tracking_url}">${frm.doc.tracking_url}</a></div>
        //         </div>`
        //     );
        // } else {
        //     $(frm.fields_dict.tracking_url_html.wrapper).html("");
        // }

        // if (frm.doc.cancel_pickup_url) {
        //     $(frm.fields_dict.cancel_pickup_url_html.wrapper).html(
        //         `<div class="form-group">
        //             <div class="clearfix"><label class="control-label" style="padding-right: 0px;">${__("Cancel pickup URL")}</label></div>
        //             <div class="control-value"><a href="${frm.doc.cancel_pickup_url}">${frm.doc.cancel_pickup_url}</a></div>
        //         </div>`
        //     );
        // } else {
        //     $(frm.fields_dict.cancel_pickup_url_html.wrapper).html("");
        // }

    },

    before_submit(frm) {
        if (!(frm.doc.shipment_parcel?.length)) {
            frappe.msgprint(__("Please specify parcels."));
        }
    },

    copy_delivery_data(frm) {
        frm.set_value('bill_to_type', frm.doc.delivery_to_type);
        frm.set_value('bill_company', frm.doc.delivery_company);
        frm.set_value('bill_customer', frm.doc.delivery_customer);
        frm.set_value('bill_supplier', frm.doc.delivery_supplier);
        frm.set_value('bill_to', frm.doc.delivery_to);
        frm.set_value('bill_address_name', frm.doc.delivery_address_name);
        frm.set_value('bill_address', frm.doc.delivery_address);
        frm.set_value('bill_contact_name', frm.doc.delivery_contact_name);
        frm.set_value('bill_contact', frm.doc.delivery_contact);

        frm.set_value('bill_company_name', frm.doc.delivery_company_name);
        frm.set_value('bill_tax_id', frm.doc.delivery_tax_id);
        frm.set_value('bill_eori_number', frm.doc.delivery_eori_number);
        frm.set_value('bill_address_line1', frm.doc.delivery_address_line1);
        frm.set_value('bill_address_line2', frm.doc.delivery_address_line2);
        frm.set_value('bill_pincode', frm.doc.delivery_pincode);
        frm.set_value('bill_city', frm.doc.delivery_city);
        frm.set_value('bill_country', frm.doc.delivery_country);
        frm.set_value('bill_contact_display', frm.doc.delivery_contact_display);
        frm.set_value('bill_contact_email_rw', frm.doc.delivery_contact_email_rw);
        frm.set_value('bill_contact_phone', frm.doc.delivery_contact_phone);
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

    add_template_custom(frm) {
        if (frm.doc.parcel_template) {
            frappe.model.with_doc("Shipment Parcel Template", frm.doc.parcel_template, () => {
                let parcel_template = frappe.model.get_doc("Shipment Parcel Template", frm.doc.parcel_template);


                // if last row is empty, use that.
                const lr = frm.doc.shipment_parcel?.slice(-1)[0];
                let row = null
                if (lr && !lr.length && !lr.width && !lr.height && !lr.weight) {
                    row = lr;
                } else {
                    row = frappe.model.add_child(frm.doc, "Shipment Parcel", "shipment_parcel");
                }

                row.parcel_template_name = parcel_template.parcel_template_name;
                row.length = parcel_template.length;
                row.width = parcel_template.width;
                row.height = parcel_template.height;
                row.weight = parcel_template.weight;
                row.is_pallet = parcel_template.is_pallet;
                frm.refresh_fields("shipment_parcel");
            });
        }
    },

    shipment_amount(frm) {
        calculate_total_value(frm);
    }
})

frappe.ui.form.on('Shipment Item', {

    qty(frm, cdt, cdn) {
        calculate_row_total(frm, cdt, cdn);
        calculate_total_value(frm);
    },

    rate(frm, cdt, cdn) {
        calculate_row_total(frm, cdt, cdn);
        calculate_total_value(frm);
    },

});

/**********************************************
 *  FORM COMPLETION HELPERS
 *********************************************/

function check_dirty(frm) {
    if (frm.is_dirty()) {
        frappe.msgprint(__('Please save document first'));
        return true;
    }
    return false
}

function calculate_row_total(frm, dt, dn) {
    let row = locals[dt][dn];
    let amount = 0
    if (row.qty && row.rate) {
        amount = row.qty * row.rate;
    }
    frappe.model.set_value(dt, dn, 'amount', amount);
}

// Keep this as indication only - recalculated server-side by a hook.
function calculate_total_value(frm) {
    const line_item_value = frm.doc.items.reduce((acc, row) => acc + row.amount, 0);
    const total = line_item_value + frm.doc.shipment_amount;

    frm.set_value('declared_value', total);
}

async function finalize_dn(frm) {
    const resp = await frappe.call({
        method: "bnovate.bnovate.utils.shipping.finalize_dn",
        args: {
            shipment_docname: frm.doc.name,
        }
    });

    frappe.set_route("Form", "Delivery Note", resp.message.name)
}

async function copy_to_rr(frm) {
    const resp = await frappe.call({
        method: "bnovate.bnovate.utils.shipping.copy_to_rr",
        args: {
            shipment_docname: frm.doc.name,
        }
    });

    frappe.set_route("Form", "Refill Request", resp.message.name)
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
        args.user = frm.doc[address_type + '_contact_person'];
    } else if (business_type === 'Customer') {
        args.customer = frm.doc[address_type + '_customer'];
        args.contact = frm.doc[address_type + '_contact_name'];
    } else if (business_type === 'Supplier') {
        args.company = frm.doc[address_type + '_supplier'];
    }

    const resp = await frappe.call({
        method: 'bnovate.bnovate.utils.shipping.fill_address_data',
        args
    })
    const fields = resp.message;

    Object.entries(fields).forEach(([k, v]) => frm.set_value(k, v));
};
window.fill_address = fill_address;

/************ PICKUP ****************/




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
    console.log(resp.message);

    frappe.msgprint(`<b>Pickup until</b>: ${estimatedPickup}<br><b>Delivery estimated on</b>: ${estimatedDelivery}<br><b>Cost estimate</b>: ${priceEstimate} ${currency}`);
    return resp.message;
}

async function create_shipment(frm, pickup = false) {

    if (check_dirty(frm))
        return;

    const resp = await bnovate.realtime.call({
        method: "bnovate.bnovate.utils.shipping.create_shipment",
        args: {
            shipment_docname: frm.doc.name,
            pickup: Number(pickup),  // or it gets passed as the string 'true' or 'false'...
        },
        callback(status) {
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

async function request_pickup(frm) {
    if (check_dirty(frm))
        return;

    const resp = await bnovate.realtime.call({
        method: "bnovate.bnovate.utils.shipping.request_pickup",
        args: {
            shipment_docname: frm.doc.name,
        },
        callback(status) {
            if (status.data.progress < 100) {
                frappe.show_progress(__("Requesting pickup..."), status.data.progress, 100, __(status.data.message));
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

async function cancel_pickup(frm) {
    if (check_dirty(frm))
        return;

    const data = await bnovate.utils.prompt(
        __("Confirm Cancellation"),
        [{
            label: __("Reason"),
            fieldname: "reason",
            fieldtype: "Data",
            reqd: 1,
        }],
        __("Cancel Pickup"),
        __("Do not cancel"),
    )

    if (!data)
        return;

    const resp = await bnovate.realtime.call({
        method: "bnovate.bnovate.utils.shipping.cancel_pickup",
        args: {
            shipment_docname: frm.doc.name,
            reason: data.reason,
        },
        callback(status) {
            if (status.data.progress < 100) {
                frappe.show_progress(__("Cancelling pickup..."), status.data.progress, 100, __(status.data.message));
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

async function update_tracking(frm) {
    const resp = await frappe.call({
        method: "bnovate.bnovate.utils.shipping.update_tracking",
        args: {
            shipment_docname: frm.doc.name,
        }
    })
    console.log(resp.message);
    frm.reload_doc();
}