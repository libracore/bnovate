/* Customisations for Company
 * 
 * Included by hooks.py to add client-side code to Sales Invoices
 * (same effect as writing a custom script)
 */

frappe.ui.form.on("Company", {
    onload(frm) {
        frm.set_query("default_address", () => {
            return {
                query: 'frappe.contacts.doctype.address.address.address_query',
                filters: {
                    link_doctype: frm.doc.doctype,
                    link_name: frm.doc.name,
                    is_your_company_address: true,
                }
            };
        })
    },
})