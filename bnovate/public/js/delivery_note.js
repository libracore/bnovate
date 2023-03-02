/* Customisations for Delivery Note
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 * - Removes legacy Create Subscription action
 */

frappe.ui.form.on("Delivery Note", {
    refresh(frm) {
        setTimeout(() => {
            frm.remove_custom_button(__("Subscription"), "Create")
            frm.add_custom_button(__("Aggregate Invoice"), async function () {
                frappe.route_options = {
                    "customer": frm.doc.customer,
                    "doctype": "Delivery Note",
                };
                await frappe.set_route("query-report", "Aggregate Invoicing");
                frappe.query_report.refresh();
            }, __("Create"));
        }, 500);
    },
})