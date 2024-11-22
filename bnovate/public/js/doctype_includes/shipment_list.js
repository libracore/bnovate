frappe.listview_settings['Shipment'] = {
    ...frappe.listview_settings['Shipment'],
    onload() {
        cur_list.page.add_inner_button("Update tracking", async () => {
            await bnovate.realtime.call({
                method: "bnovate.bnovate.utils.shipping.update_tracking_undelivered",
                callback(status) {
                    if (status.data.progress < 100) {
                        frappe.show_progress(__("Updating..."), status.data.progress, 100, __(status.data.message));
                    }
                    if (status.code == 0) {
                        frappe.hide_progress();
                    }
                }
            });
            cur_list.refresh();
        })
    },
    get_indicator(doc) {
        /* CUSTOM STATUSES

        - Registered: Shipment data has been registered with the carrier (shipment "created" on their platform)
        - Completed: Pickup has been requested -- our work is done.

        */

        if (doc.status == 'Booked') {
            return [__("Booked"), "orange"];
        }
        if (doc.status == 'Registered') {
            return [__("Registered"), "orange"];
        };

        if (doc.status == 'Completed') {
            return [__("Completed"), "green"];
        };
    }
}