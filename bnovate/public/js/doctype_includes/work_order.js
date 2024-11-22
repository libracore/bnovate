/* Customisations for Work Order
 * 
 * Included by hooks.py to add client-side code
 * 
 * - Set target warehouse to Quality Control if inspection needed
 * Note that we hide the default ERPNext inspection system and use "QC required" instead.
 */


frappe.ui.form.on("Work Order", {
    // qc_required(frm) {
    //     console.log(frm.doc, frm.doc.production_item);
    // },
})