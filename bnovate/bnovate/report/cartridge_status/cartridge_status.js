// Copyright (c) 2023, bnovate, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Cartridge Status"] = {
    filters: [
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "serial_no",
            "label": __("Serial No"),
            "fieldtype": "Link",
            "options": "Serial No"
        },
        {
            "fieldname": "only_stored",
            "label": __("At bNovate only"),
            "fieldtype": "Check",
            "default": 0
        },
    ]
};
