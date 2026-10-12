/* Customisations for Item
 * 
 * Included by hooks.py to add client-side code to Sales Invoices
 * (same effect as writing a custom script)
 */

frappe.require("/assets/bnovate/js/step_viewer.js")  // provides bnovate.step

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

        frm.add_custom_button("BOM Search (bN)", function () {
            frappe.route_options = {
                item1: frm.doc.name,
            };
            frappe.set_route("query-report", "BOM Search (bN)");
        }, __("View"));

        frm.add_custom_button("BOM Stock Report (bN)", async function () {
            frappe.route_options = {
                bom: frm.doc.default_bom,
                warehouse: "Available Stock - bN",
            };
            frappe.set_route("query-report", "BOM Stock Report (bN)");
        }, __("View"));

        if (!frm.is_new()) {
            frm.add_custom_button(__("STEP files"), () => show_step_files(frm), __("View"));
        }

    },

    onload_post_render(frm) {
        frm.remove_custom_button("BOM Search", __("View"));

    }
})

function show_step_files(frm) {
    // Attachments in STEP format
    const files = frm.get_files().filter(bnovate.step.is_step_file);
    if (!files.length) {
        frappe.msgprint(__("This item has no STEP files attached."));
        return;
    }
    bnovate.step.show({ title: __("STEP files") + " - " + frm.doc.name, files });
}
