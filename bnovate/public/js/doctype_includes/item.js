/* Customisations for Item
 * 
 * Included by hooks.py to add client-side code to Sales Invoices
 * (same effect as writing a custom script)
 */

frappe.ui.form.on("Item", {
    before_load(frm) {
        frm.dashboard.add_transactions({
            'items': ['Subscription Contract'],
            'label': 'Sell',
        })
    },

    refresh(frm) {

        // Look for item defaults for this company
        const default_company = bnovate.utils.get_default_company();
        const item_defaults = frm.doc.item_defaults.find(it => it.company == default_company);

        frm.add_custom_button("Projected Stock", function () {
            // Find item default for currenct default company
            frappe.route_options = {
                item_code: frm.doc.name,
                warehouse: item_defaults?.default_warehouse,
            };
            console.log(frappe.route_options)
            frappe.set_route("query-report", "Projected Stock");
        });

        frm.add_custom_button("BOM Search", function () {
            frappe.route_options = {
                item1: frm.doc.name,
            };
            frappe.set_route("query-report", "BOM Search (bN)");
        }, __("View"));

    },
})