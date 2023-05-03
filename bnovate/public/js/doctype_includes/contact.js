/* Customisations for Contact
 * 
 * Included by hooks.py
 */

frappe.ui.form.on("Contact", {
    async validate(frm) {
        if (frm.doc.user) {
            const matches = await frappe.db.get_list("Contact", {
                filters: {
                    user: frm.doc.user,
                    name: ['NOT LIKE', frm.doc.name],
                }
            });
            if (matches.length) {
                const links = matches.map(m => frappe.utils.get_form_link("Contact", m.name, true, m.name))
                frappe.validated = false;
                frappe.msgprint({
                    indicator: 'red',
                    title: __('Error'),
                    message: __('User ID is already associated with another contact: ') + links.join(", "),
                });
                return;
            }
        }
    },
})