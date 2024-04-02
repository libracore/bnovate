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

    console.log(resp.message);
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