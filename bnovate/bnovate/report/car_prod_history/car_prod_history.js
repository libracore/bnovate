// Copyright (c) 2021, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CAR prod history"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default" : new Date((new Date()).getFullYear(), 0, 1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default" : new Date((new Date()).getFullYear(), 11, 31),
            "reqd": 1
        }
    ]
};
