/* Customisations for Stock Entry
 * 
 * Included by hooks.py to add client-side code
 * 
 * - Add cartridge routing label print.
 */



frappe.ui.form.on("Stock Entry", {
    refresh(frm) {
        frm.add_custom_button('<i class="fa fa-print"></i> ' + __('Routing Label'), () => {
            get_label(frm.doc.doctype, frm.doc.name, "Cartridge Routing Label", "Labels 100x30mm");
        });
    },
})

