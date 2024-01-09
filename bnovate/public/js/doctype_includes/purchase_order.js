/* Customisations for Purchase Order
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 */


frappe.ui.form.on("Purchase Order", {
    onload(frm) {

        frm.set_query("blanket_order", "items", function () {
            return {
                filters: {
                    "company": frm.doc.company,
                    "docstatus": 1,
                    "supplier": frm.doc.supplier,
                    "currency": ["IN", [frm.doc.currency, ""]]
                }
            }
        });

    },

})
