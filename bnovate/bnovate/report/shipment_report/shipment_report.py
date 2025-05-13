# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters or {})
	return columns, data

def get_columns():
	return [
		{"label": "Shipment ID", "fieldname": "name", "fieldtype": "Data", "width": 120},
		{"label": "Pickup Company", "fieldname": "pickup_company_name", "fieldtype": "Data", "width": 150},
		{"label": "Delivery Company", "fieldname": "delivery_company_name", "fieldtype": "Data", "width": 150},
		{"label": "Pickup Date", "fieldname": "pickup_date", "fieldtype": "Date", "width": 120},
		{"label": "AWB Number", "fieldname": "awb_number", "fieldtype": "Data", "width": 120},
		{"label": "Tracking Stage", "fieldname": "tracking_stage", "fieldtype": "Data", "width": 150},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
	]

def get_data(filters):
	conditions = []
	if filters.get("customer"):
		conditions.append("""
			(pickup_customer = "{customer}" OR 
			delivery_customer = "{customer}" OR 
			bill_customer = "{customer}")
		""".format(customer=filters.customer))
	conditions_str = " AND ".join(conditions) if conditions else "1=1"

	return frappe.db.sql("""
		SELECT
			name,
			pickup_company_name,
			delivery_company_name,
			pickup_date,
			awb_number,
			tracking_stage,
			status
		FROM
			`tabShipment`
		WHERE
			{conditions_str}
		ORDER BY name DESC
	""".format(conditions_str=conditions_str), as_dict=True)
