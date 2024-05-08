frappe.listview_settings['Shipment'] = {
    ...frappe.listview_settings['Shipment'],
    onload() {
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