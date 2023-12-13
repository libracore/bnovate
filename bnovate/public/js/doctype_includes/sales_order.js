/* Customisations for Sales Order
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 * - Removes legacy Create Subscription action
 */

frappe.require("/assets/bnovate/js/modals.js")  // provides bnovate.modals

frappe.ui.form.on("Sales Order", {
    async before_load(frm) {
        frm.dashboard.add_transactions({
            'items': ['Refill Request'],
            'label': 'Reference',
        });

        // Hijack formatter, we'll set colours according to deliverability later.
        frm.set_indicator_formatter('item_code', (doc) => "");
    },

    async refresh(frm) {
        setTimeout(() => {
            frm.remove_custom_button("Subscription", "Create")
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
            return frm.call({
                doc: frm.doc,
                method: "apply_custom_shipping_rule",
                callback: function (r) {
                }
            }).fail();
        }
        else {
            frm.cscript.calculate_taxes_and_totals();
        }

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