/* Customisations for Serial No
 * 
 * Included by hooks.py to add client-side code
 * 
 * - Displays cartridge status in flow chart form
 */


frappe.require("/assets/bnovate/js/flowchart.js")

frappe.ui.form.on("Serial No", {
    async refresh(frm) {
        const report_data = await get_status(frm.doc.serial_no);
        if (report_data.result && report_data.result.length) {
            bnovate.flowchart.attach(
                frm.fields_dict.cartridge_flowchart.wrapper,
                report_data.result[0].order_status,
                report_data.result[0].status,
            );
        }
    },

    status_details(frm) {
        frappe.route_options = { serial_no: frm.doc.serial_no };
        frappe.set_route("query-report", "Cartridge Status");
    },
})

async function get_status(serial_no) {
    // Fetch report data
    let resp = await frappe.call({
        method: "frappe.desk.query_report.run",
        args: {
            report_name: "Cartridge Status",
            filters: {
                serial_no
            }
        }
    })
    return resp.message;
}