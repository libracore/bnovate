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
    setup(frm) {
        frm.set_query('portal_billing_address', function (doc) {
            return {
                query: 'frappe.contacts.doctype.address.address.address_query',
                filters: {
                    link_doctype: 'Customer',
                    link_name: doc.name
                }
            };
        })
    }
})