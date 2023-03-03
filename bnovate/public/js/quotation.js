/* Customisations for Quotation
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 * - Removes legacy Create Subscription action
 */

frappe.ui.form.on("Quotation", {
    setup(frm) {
        frm.custom_make_buttons['Subscription Service'] = 'Make Subscription';
        cur_frm.cscript['Make Subscription'] = function () {
            frappe.model.open_mapped_doc({
                method: "erpnext.selling.doctype.quotation.quotation.make_sales_order",
                frm: cur_frm
            })
        }
    },
    refresh(frm) {
        setTimeout(() => {
            frm.remove_custom_button("Subscription", "Create")
        }, 500);
    },
})