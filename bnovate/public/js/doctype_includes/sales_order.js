/* Customisations for Sales Order
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 */

frappe.require("/assets/bnovate/js/modals.js")  // provides bnovate.modals
frappe.require("/assets/bnovate/js/shipping.js")  // provides bnovate.shipping

frappe.ui.form.on("Sales Order", {
    async before_load(frm) {
        frm.dashboard.add_transactions({
            'items': ['Refill Request'],
            'label': 'Reference',
        });

        frm.dashboard.add_transactions({
            'items': ['Shipment'],
            'label': 'Fulfillment',
        });

        // Hijack formatter, we'll set colours according to deliverability later.
        frm.set_indicator_formatter('item_code', (doc) => "");
    },

    onload(frm) {

        frm.set_query("custom_shipping_rule", () => {
            return {
                filters: {
                    country: frm.doc.shipping_country,
                    company: frm.doc.company,
                }
            }
        })

        frm.set_query("blanket_order", "items", function () {
            return {
                filters: {
                    "company": frm.doc.company,
                    "docstatus": 1,
                    "to_date": [">=", frm.doc.transaction_date],
                    "from_date": ["<=", frm.doc.transaction_date],
                    "customer": frm.doc.customer,
                    "currency": ["IN", [frm.doc.currency, ""]]
                }
            }
        });

        if (frm.doc.tc_name && !frm.doc.terms) {
            // Trigger copying of template
            frm.trigger('tc_name');
        }

    },

    async refresh(frm) {
        setTimeout(() => {
            frm.remove_custom_button(__("Subscription"), __("Create"));
        }, 500);

        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Refill Request'),
                function () {
                    erpnext.utils.map_current_doc({
                        method: "bnovate.bnovate.doctype.refill_request.refill_request.make_sales_order",
                        source_doctype: "Refill Request",
                        target: frm,
                        setters: [
                            {
                                label: "Customer",
                                fieldname: "customer",
                                fieldtype: "Link",
                                options: "Customer",
                                default: frm.doc.customer || undefined
                            }
                        ],
                        get_query_filters: {
                            docstatus: 1,
                            status: "Submitted", // Ignore already confirmed orders
                        }
                    })
                }, __("Get items from"));

        }

        frm.add_custom_button(__('Return Shipment'), () => create_return_shipment(frm), __("Create"));

        // Show cartridges owned by this customer in a modal
        bnovate.modals.attach_report_modal("cartStatusModal");
        frm.fields_dict.view_stored_cartridges.wrapper.innerHTML = bnovate.modals.report_link(
            '<button class="btn btn-default btn-xs">View Cartridges</button>',
            'cartStatusModal',
            'Cartridge Status',
            'Catridges owned by this customer',
            {
                'customer': frm.doc.customer
            }

        );

        bnovate.modals.attach_report_modal("projStockModal");
        if (!frm.doc.__islocal) {
            setTimeout(() => show_deliverability(frm), 500);
        }
    },

    async before_submit(frm) {

        // If incoterm requires that we ship, check deliverability:
        if (frm.doc.incoterm === "DAP" || frm.doc.incoterm === "DDP") {
            const err = await bnovate.shipping.validate_sales_order(frm.doc.name);
            if (err.error) {
                frappe.msgprint(err.error + ":<br><br>" + err.message);
                frappe.validated = false;
            }
        }
    },

    async customer(frm) {
        // Fetch default terms from customer group
        const customer_doc = await frappe.model.with_doc("Customer", frm.doc.customer);
        const customer_group = await frappe.model.with_doc("Customer Group", customer_doc.customer_group);

        setTimeout(() => {
            frm.set_value('taxes_and_charges', customer_group.taxes_and_charges_template);
        }, 500)
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

    taxes_and_charges(frm) {
        // Re-calculate shipping. FIXME: race condition.
        // frm.trigger('custom_shipping_rule');
        // console.log('Should have triggered taxes refresh');
    },

})

async function get_deliverability(frm) {
    const report_data = await bnovate.utils.run_report('Orders to Fulfill', { sales_order: frm.doc.name, include_drafts: 1 });
    let d = {}
    for (let row of report_data.result) {
        d[row.detail_docname] = row;
    }
    return d;
}

async function show_deliverability(frm) {
    const deliverability = await get_deliverability(frm);
    for (let item of cur_frm.doc.items) {
        const indicator = document.querySelector(`[data-name="${item.name}"] .indicator`)
        let colour = "darkgrey";
        let planned_stock = "";
        let status = deliverability[item.name];
        if (item.stock_qty <= item.delivered_qty) {
            colour = "light-blue";
        } else if (typeof status !== undefined) {
            colour = ["red", "orange", "yellow", "green"][status.sufficient_stock];
            if (status.guaranteed_stock !== null && status.projected_stock !== null) {
                const stock_field = document.querySelector(`[data-name="${item.name}"] [data-fieldname="planned_stock"]`)
                if (stock_field) {
                    stock_field.innerHTML = `<span class="coloured" style="text-align: center; padding-top: 10px"><a>${status.projected_stock} | ${status.guaranteed_stock}</a></span>`;
                    stock_field.firstChild.addEventListener('click', (event) => {
                        event.stopImmediatePropagation();
                        event.preventDefault();
                        bnovate.modals.show('projStockModal',
                            'Projected Stock',
                            `Projected Stock for Item ${item.item_code}: ${item.item_name}`,
                            {
                                'item_code': item.item_code,
                                'so_drafts': true,
                                // 'warehouse': item.warehouse,
                            }
                        );
                    });
                }
            }
        }
        indicator.classList.add(colour);
    }
}


async function prompt_label_format(frm) {
    const data = await bnovate.utils.prompt(
        __("Confirm Label Format"),
        [{
            label: __("Label Size"),
            fieldname: "label_format",
            fieldtype: "Select",
            options: "8x4 inch\nA4",
            default: "A4",
            reqd: 1,
        }],
        "Confirm",
        "Cancel",
    )
    return data;
}

async function create_return_shipment(frm) {

    const args = await prompt_label_format(frm);
    if (args === null) {
        return
    }

    // Since we allow this on draft, we haven't yet validated the SO for delivery creation
    const err = await bnovate.shipping.validate_sales_order(frm.doc.name);
    if (err.error) {
        frappe.msgprint(err.error + ":<br><br>" + err.message);
        return
    }

    frappe.model.open_mapped_doc({
        method: "bnovate.bnovate.utils.shipping.make_return_shipment_from_so",
        frm,
        args,
    })
}