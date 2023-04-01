// render
frappe.listview_settings['Subscription Contract'] = {
    get_indicator: function (doc) {
        var status_color = {
            "Draft": "red",
            "Active": "green",
            "Finished": "darkgrey",
            "Stopped": "darkgrey",
        };
        return [__(doc.status), status_color[doc.status], "status,=," + doc.status];
    },
};
