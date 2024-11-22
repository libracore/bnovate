/* Customisations for Address
 * 
 * Included by hooks.py to add client-side code
 */

frappe.require("/assets/bnovate/js/shipping.js")  // provides bnovate.shipping

frappe.ui.form.on("Address", {

    refresh(frm) {
        frm.add_custom_button(__("Check Address"), async function () {
            return await validate_address(frm);
        });
    },
})

async function validate_address(frm) {

    if (frm.is_dirty()) {
        frappe.msgprint(__('Please save document first'));
        return;
    }

    try {
        const resp = await frappe.call({
            method: 'bnovate.bnovate.utils.shipping.validate_address',
            args: {
                name: frm.doc.name
            }
        })
    } catch (e) {
        // Error message is displayed anyway.
        return;
    }

    // If no error raised, Address is shippable
    frappe.msgprint(__("Address is deliverable"))
}