// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Enclosure Filling History"] = {
	"filters": [
        {
            "fieldname": "serial_no",
            "label": __("Serial no"),
            "fieldtype": "Link",
            "options" : "Serial No"
        }
	]
};