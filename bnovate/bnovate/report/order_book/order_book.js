// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Order Book"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": new Date((new Date()).getFullYear(), 0, 1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": new Date((new Date()).getFullYear(), 11, 31),
            "reqd": 1
        },
        {
            "fieldname": "period_length",
            "label": __("Period Length"),
            "fieldtype": "Select",
            "options": [
                { "value": "month", "label": __("Month") },
                { "value": "quarter", "label": __("Quarter") },
                { "value": "year", "label": __("Year") },
            ],
            "default": "month",
            "reqd": 1
        },
        {
            "fieldname": "sum_type",
            "label": __("Value or Qty"),
            "fieldtype": "Select",
            "options": [
                { "value": "value", "label": __("Value") },
                { "value": "qty", "label": __("Quantity") },
            ],
            "default": "value",
            "reqd": 1
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group"
        }
    ]
};
