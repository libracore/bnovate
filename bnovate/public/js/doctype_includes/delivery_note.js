/* Customisations for Delivery Note
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 * - Removes legacy Create Subscription action
 * - Handles 'packing_stage' field: show when a DN is ready for pickup to be arranged.
 * 
 * 
 *  Workflow: 
 *      - Document is submitted when package is ready to leave, so as to validate and update stock.
 *      - 'Packing stage' changes to 'Ready to Ship'
 *      - Once shipped, stage changes to 'Shipped' and tracking info is updated.
 */

frappe.ui.form.on("Delivery Note", {

    before_load(frm) {
        frm.override_action_buttons = () => override_action_buttons(frm);
        frm.assign = () => assign(frm);

        frm.override_action_buttons();

        frm.dashboard.add_transactions({
            'items': ['Shipment'],
            'label': 'Related',
        });
    },

    onload(frm) {
        frm.set_query("custom_shipping_rule", () => {
            return {
                filters: {
                    country: frm.doc.shipping_country,
                }
            }
        })
    },

    refresh(frm) {
        setTimeout(() => {
            frm.remove_custom_button(__("Subscription"), __("Create"));
            frm.add_custom_button(__("Aggregate Invoice"), async function () {
                frappe.route_options = {
                    "customer": frm.doc.customer,
                    "doctype": "Delivery Note",
                };
                await frappe.set_route("query-report", "Aggregate Invoicing");
                frappe.query_report.refresh();
            }, __("Create"));

            // Override standard delivery creation
            frm.remove_custom_button(__("Shipment"), __("Create"));
            frm.add_custom_button(__("Shipment"), () => create_shipment(frm), __("Create"));
        }, 500);

        frm.override_action_buttons()
    },

    custom_shipping_rule(frm) {

        // Call Custom Shipping Rule instead of built-in one:
        if (frm.doc.custom_shipping_rule) {
            return frappe.call({
                method: 'bnovate.bnovate.doctype.custom_shipping_rule.custom_shipping_rule.apply_rule',
                args: {
                    doc: frm.doc,
                },
                callback: (r) => {
                    if (!r.exc) {
                        frm.refresh_fields();
                        frm.cscript.calculate_taxes_and_totals();
                    }
                },
                error: () => frm.set_value('custom_shipping_rule', ''),
            })
        }
        else {
            frm.cscript.calculate_taxes_and_totals();
        }

    },
})

function create_shipment(frm) {
    frappe.model.open_mapped_doc({
        method: "bnovate.bnovate.utils.shipping.make_shipment_from_dn",
        frm
    })
}

function override_action_buttons(frm) {

    if (frm.is_dirty()) {
        return;
    }

    if (frm.doc.docstatus === 1) {
        // Only override action button if form is submitted
        frm.page.clear_primary_action();
        if (frm.doc.packing_stage == "Packing") {
            frm.page.set_primary_action(__("Request Pickup"), async () => {
                // TODO: set tracking info and stage
                frm.doc.packing_stage = 'Ready to Ship';
                frm.save("Update");
                await frm.assign();
            })
        } else if (frm.doc.packing_stage == "Ready to Ship") {
            frm.page.set_primary_action(__("Confirm Shipment"), async () => {
                const values = await bnovate.utils.prompt("Enter shipping details",
                    [{
                        label: "Carrier",
                        fieldname: "carrier",
                        fieldtype: "Data",
                        reqd: 0,
                        default: frm.doc.carrier || "DHL",
                    }, {
                        label: "Tracking No",
                        fieldname: "tracking_no",
                        fieldtype: "Data",
                        reqd: 0,
                        default: frm.doc.tracking_no,
                    }],
                    "Confirm",
                    "Cancel"
                )
                frm.doc.packing_stage = 'Shipped';
                frm.doc.carrier = values.carrier;
                frm.doc.tracking_no = values.tracking_no;
                frm.save("Update");
                bnovate.utils.email_dialog(frm, await bnovate.utils.get_setting('dn_template'));
            })
        }
    }
};

async function assign(frm) {
    if (frm.is_new()) {
        frappe.throw(__("Please save the document before assignment"));
        return;
    }

    return new Promise((resolve, reject) => {
        const assign_to = new frappe.ui.form.AssignToDialog({
            obj: frm,
            method: 'frappe.desk.form.assign_to.add',
            doctype: frm.doctype,
            docname: frm.docname,
            callback: function (r) {
                resolve();
                me.render(r.message);
            }
        });
        // me.assign_to.dialog.clear();

        if (frm.meta.title_field) {
            assign_to.dialog.set_value("description", me.frm.doc[me.frm.meta.title_field])
        }

        assign_to.dialog.show();
    });
}