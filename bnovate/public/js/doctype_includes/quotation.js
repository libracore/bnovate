/* Customisations for Quotation
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 * 
 * - Removes legacy Create Subscription action
 */

frappe.ui.form.on("Quotation", {
    before_load(frm) {
        frm.dashboard.add_transactions({
            'items': ['Subscription Contract'],
            'label': 'Subscription',
        });
    },
    onload(frm) {
        frm.set_query("custom_shipping_rule", () => {
            return {
                filters: {
                    country: frm.doc.shipping_country,
                }
            }
        })
    },
    setup(frm) {
        frm.custom_make_buttons['Subscription'] = 'Make Subscription';
        frm.cscript['Make Subscription'] = function () {
            frappe.model.open_mapped_doc({
                method: "bnovate.bnovate.doctype.subscription_contract.subscription_contract.make_from_quotation",
                frm: cur_frm
            });
        }
    },
    refresh(frm) {
        setTimeout(() => {
            frm.remove_custom_button("Subscription", "Create")
            if (frm.doc.docstatus == 1 && frm.doc.status !== 'Lost') {
                if (!frm.doc.valid_till || frappe.datetime.get_diff(frm.doc.valid_till, frappe.datetime.get_today()) >= 0) {
                    frm.add_custom_button(__('Subscription'),
                        frm.cscript['Make Subscription'], __('Create'));
                }
            };
        }, 500);
    },
    custom_shipping_rule(frm) {
        if (frm.doc.custom_shipping_rule) {
            return frappe.call({
                method: 'bnovate.bnovate.doctype.custom_shipping_rule.custom_shipping_rule.apply_rule',
                args: {
                    doc: frm.doc,
                },
                callback: (r) => {
                    if (!r.exc) {
                        frm.refresh_fields();
                        frm.cscript.calculate_taxes_and_totals();
                    }
                },
                error: () => frm.set_value('custom_shipping_rule', ''),
            })
        } else {
            frm.cscript.calculate_taxes_and_totals();
        }

    },

})