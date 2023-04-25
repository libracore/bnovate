/* Customisations for Sales Order
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 * - Removes legacy Create Subscription action
 */

frappe.ui.form.on("Sales Order", {
    before_load(frm) {
        // frm.dashboard.add_transactions({
        //     'items': ['Refill Request'],
        //     'label': 'Reference',
        // })
        // frm.dashboard.data.internal_links['Refill Request'] = ['items', 'refill_request'];
    },
    refresh(frm) {
        setTimeout(() => {
            frm.remove_custom_button("Subscription", "Create")
        }, 500);
    },
})