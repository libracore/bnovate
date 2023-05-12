/* Customisations for Customer
 * 
 * Included by hooks.py to add client-side code to Sales Invoices
 * (same effect as writing a custom script)
 */

frappe.ui.form.on("Customer", {
    before_load(frm) {
        frm.dashboard.add_transactions({
            'items': ['Subscription Contract', 'Connectivity Package'],
            'label': 'Orders',
        })
    },
})