// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Orders to Fulfill"] = {
	"filters": [
		{
            "fieldname": "only_manufacturing",
            "label": __("Only manufactured items"),
            "fieldtype": "Check",
            "default" : 1
        },
	]
};
