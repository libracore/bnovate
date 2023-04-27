frappe.listview_settings['Refill Request'] = {
    get_indicator: function (doc) {
        var status_color = {
            "Draft": "red",
            "Requested": "orange",
            "Confirmed": "blue",
            "Shipped": "green",
            "Cancelled": "darkgrey",
        };
        return [__(doc.status), status_color[doc.status], "status,=," + doc.status];
    },
}