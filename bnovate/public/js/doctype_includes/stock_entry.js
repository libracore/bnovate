/* Customisations for Stock Entry
 * 
 * Included by hooks.py to add client-side code
 * 
 * - Add cartridge routing label print.
 */



frappe.ui.form.on("Stock Entry", {
    async refresh(frm) {
        frm.add_custom_button('<i class="fa fa-print"></i> ' + __('Routing Label'), () => {
            get_label(frm.doc.doctype, frm.doc.name, "Cartridge Routing Label", "Labels 100x30mm");
        });

        if (frm.doc.docstatus === 0 && frm.doc.purpose == "Material Issue") {
            frm.remove_custom_button(__('Expired Batches'), __("Get items from"));
            frm.add_custom_button(__('Expired Batches') + ' (bN)', async function () {
                const resp = await frappe.call({
                    method: "erpnext.stock.doctype.stock_entry.stock_entry.get_expired_batch_items",
                });

                if (resp.exc || !resp.message) {
                    frappe.show_alert({
                        message: __('No expired batches found'),
                        indicator: 'red'
                    });
                    return;
                }

                frm.set_value("items", []);
                resp.message.filter(element => element.qty > 0)
                    .forEach(function (element) {
                        let d = frm.add_child("items");
                        d.item_code = element.item;
                        d.s_warehouse = element.warehouse;
                        d.qty = element.qty;
                        d.uom = element.stock_uom;
                        d.conversion_factor = 1;
                        d.batch_no = element.batch_no;
                        d.transfer_qty = element.qty;
                        frm.refresh_fields();
                    })
            }, __("Get items from"));
        }
    }
})

