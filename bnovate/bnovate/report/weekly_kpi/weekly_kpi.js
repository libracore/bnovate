// Copyright (c) 2022, libracore, bNovate and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Weekly KPI"] = {
    "filters": [
        {
            "fieldname": "year",
            "label": __("Year"),
            "fieldtype": "Int",
            "default" : (new Date()).getFullYear(),
            "reqd": 1
        }
    ]
};
