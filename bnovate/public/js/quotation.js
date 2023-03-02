/* Customisations for Quotation
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 * - Removes legacy Create Subscription action
 */

frappe.ui.form.on("Quotation", {
    refresh(frm) {
        setTimeout(() => {
            frm.remove_custom_button("Subscription", "Create")
        }, 500);
    },
})