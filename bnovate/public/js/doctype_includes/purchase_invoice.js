/* Customisations for Purchase Invoice
 * 
 * Included by hooks.py to add client-side code to Purchase Invoices
 * (same effect as writing a custom script)
 * 
 */

frappe.ui.form.on("Purchase Invoice", {
    refresh(frm) {
        frm.add_custom_button(__('Deferred Expense Entries'), async function () {
            await bnovate.utils.book_deferred_income_or_expense(frm.doc.doctype, frm.doc.name);
        }, __('Create'))
    },
})