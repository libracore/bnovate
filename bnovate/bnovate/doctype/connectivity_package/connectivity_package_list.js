
frappe.listview_settings['Connectivity Package'] = {
    onload(lv) {
        lv.page.add_inner_button(__("View Map"), () => {
            frappe.set_route("device-map");
        });
    },
}