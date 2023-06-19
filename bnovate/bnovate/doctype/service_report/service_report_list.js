frappe.listview_settings['Service Report'] = {
    onload() {
    },
    async primary_action() {
        const values = await prompt_from_template();
        console.log("Override primary action", values);
        if (values.template) {
            frappe.model.open_mapped_doc({
                method: "bnovate.bnovate.doctype.service_report.service_report.make_from_template",
                frm: { // hack so that open_mapped_doc works.
                    doc: { __unsaved: false },
                    get_selected() { return null; },

                },
                source_name: values.template,
            });
        } else {
            frappe.set_route("Form", "Service Report", "New Service Report");
        }
    },
}


function prompt_from_template() {
    return bnovate.utils.prompt(
        "Select Template (or nothing for a blank report)",
        [{
            "fieldname": "template",
            "fieldtype": "Link",
            "label": "Template",
            "options": "Service Report Template"
        }],
        "New",
        "Cancel",
    )
}