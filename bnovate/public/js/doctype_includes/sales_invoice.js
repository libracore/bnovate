/* Customisations for Sales Invoice
 * 
 * Included by hooks.py to add client-side code to Sales Invoices
 * (same effect as writing a custom script)
 * 
 * - Shows Subscription Contract in dashboard
 * - Removes legacy Create Subscription action
 */

frappe.ui.form.on("Sales Invoice", {
    before_load(frm) {
        frm.dashboard.add_transactions({
            'items': ['Subscription Contract'],
            'label': 'Subscription',
        })
        frm.dashboard.data.internal_links['Subscription Contract'] = ['items', 'subscription'];
    },
    refresh(frm) {
        setTimeout(() => {
            frm.remove_custom_button("Subscription", "Create")
        }, 500);

        frm.add_custom_button(__('Deferred Revenue Entries'), async function () {
            await bnovate.utils.book_deferred_income_or_expense(frm.doc.doctype, frm.doc.name);
        }, __('Create'))


    },
})