// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Projected Stock"] = {
    "filters": [
        {
            "fieldname": "item_code",
            "label": __("Item Code"),
            "fieldtype": "Link",
            "options": "Item"
        }, {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse"
        },
        {
            "fieldname": "so_drafts",
            "label": __("Include SO Drafts"),
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "wo_drafts",
            "label": __("Include WO Drafts"),
            "fieldtype": "Check",
            "default": 0
        },
    ]
};
