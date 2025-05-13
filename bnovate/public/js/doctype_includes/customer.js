/* Customisations for Customer
 * 
 * Included by hooks.py to add client-side code to Sales Invoices
 * (same effect as writing a custom script)
 */

frappe.ui.form.on("Customer", {
    before_load(frm) {
        frm.dashboard.add_transactions({
            'items': ['Subscription Contract', 'Connectivity Package', 'Refill Request', 'Blanket Order', 'Serial No', 'License Key'],
            'label': 'Orders',
        })
        frm.dashboard.add_transactions({
            'items': ['Service Report'],
            'label': 'Support',
        })
    },
    setup(frm) {
        frm.set_query('portal_billing_address', function (doc) {
            return {
                query: 'frappe.contacts.doctype.address.address.address_query',
                filters: {
                    link_doctype: 'Customer',
                    link_name: doc.name
                }
            };
        })
    },
    refresh(frm) {
        frm.add_custom_button(__("Stored Cartridges"), function () {
            frappe.route_options = { customer: frm.doc.name, only_stored: true };
            frappe.set_route("query-report", "Cartridge Status");
        }, __("View"));

        frm.add_custom_button(__("Shipments"), function () {
            frappe.route_options = { customer: frm.doc.name };
            frappe.set_route("query-report", "Shipment Report");
        }, __("View"));
    },
    check_eori(frm) {
        // If API is unreliable, we could just link to the EU website:
        // window.open('https://ec.europa.eu/taxation_customs/dds2/eos/eori_validation.jsp?Lang=en&EoriNumb=' + frm.doc.eori_number, '_blank');

        bnovate.utils.check_eori(frm.doc.eori_number);
    }
})