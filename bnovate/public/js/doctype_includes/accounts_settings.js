/* Customisations for Accounts Settings
 * 
 * Included by hooks.py to add client-side code
 */


frappe.ui.form.on("Accounts Settings", {

    refresh(frm) {
        frm.add_custom_button(__("Apply Deferred Revenue"), async function () {
            return await bnovate.utils.convert_deferred_revenue_to_income();
        });

        frm.add_custom_button(__("Apply Deferred Expense"), async function () {
            return await bnovate.utils.convert_deferred_expense_to_expense();
        });
    },
})