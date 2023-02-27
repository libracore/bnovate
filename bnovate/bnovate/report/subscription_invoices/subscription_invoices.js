// Copyright (c) 2023, bNovate, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Subscription Invoices"] = {
    filters: [
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "subscription",
            "label": __("Subscription"),
            "fieldtype": "Link",
            "options": "Subscription Service"
        },
    ]
};
