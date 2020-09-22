// Copyright (c) 2016-2020, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Enclosure History"] = {
	"filters": [
        {
            "fieldname": "snr",
            "label": __("Serial no"),
            "fieldtype": "Link",
            "options" : "Serial No"
        }
	]
};
