frappe.listview_settings['Refill Request'] = {
    get_indicator: function (doc) {
        var status_color = {
            "Draft": "red",
            "Submitted": "orange",
            "Confirmed": "green",
            "Shipped": "green",
            "Cancelled": "darkgrey",
        };
        return [__(doc.status), status_color[doc.status], "status,=," + doc.status];
    },
}