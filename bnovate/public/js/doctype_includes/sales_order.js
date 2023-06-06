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

        // Disable built-in indicator formatter, will be replaced lower by report data
        const deliverability = await get_deliverability(frm);
        console.log(deliverability);
        frm.set_indicator_formatter('item_code', (doc) => {
            console.log("formatter called", doc)
            if (doc.stock_qty <= doc.delivered_qty) {
                return "light-blue";
            } else if (typeof deliverability[doc.name] !== undefined) {
                return ["red", "orange", "yellow", "green"][deliverability[doc.name]];
            } else {
                return "darkgrey"
            }
        });
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
    },
})

async function get_deliverability(frm) {
    const report_data = await bnovate.utils.run_report('Orders to Fulfill', { sales_order: frm.doc.name, include_drafts: 1 });
    let d = {}
    for (let row of report_data.result) {
        d[row.detail_docname] = row.sufficient_stock;
    }
    return d;
}