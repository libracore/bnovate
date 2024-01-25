/* Customisations for Blanket Order
 * 
 * Included by hooks.py
 */

frappe.ui.form.on("Blanket Order", {
    refresh(frm) {

        // Monkey patch currency in items table to ensure display is correct
        frm.fields_dict.items.grid.fields_map.rate.options = 'currency';
        frm.refresh_field('items');
    },

    currency(frm) {
        // Redraw currency symbol
        frm.refresh_field('items');
    }
})