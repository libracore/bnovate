# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe


def execute(filters=None):
    columns, data = get_columns(), get_data()
    return columns, data


def get_columns():
    return [
        {'fieldname': 'item_code', 'label': 'Item Code', 'fieldtype': 'Link', 'width': 120, 'options': 'Item'},
        {'fieldname': 'item_name', 'label': 'Item Name', 'fieldtype': 'Data', 'width': 120},
        {'fieldname': 'original_item_name', 'label': 'Original Item Name', 'fieldtype': 'Data', 'width': 120},
        {'fieldname': 'item_group', 'label': 'Item Group', 'fieldtype': 'Link', 'width': 120, 'options': 'Item Group'},
        {'fieldname': 'description', 'label': 'Description', 'fieldtype': 'Data', 'width': 150},
        {'fieldname': 'qty', 'label': 'Qty', 'fieldtype': 'Data', 'width': 100},
        {'fieldname': 'uom', 'label': 'UOM', 'fieldtype': 'Link', 'width': 80, 'options': 'UOM'},
        {'fieldname': 'base_rate', 'label': 'Rate', 'fieldtype': 'Currency', 'width': 120},
        {'fieldname': 'base_amount', 'label': 'Amount', 'fieldtype': 'Currency', 'width': 120},
        {'fieldname': 'so_name', 'label': 'Sales Order', 'fieldtype': 'Link', 'width': 120, 'options': 'Sales Order'},
        {'fieldname': 'so_date', 'label': 'SO Date', 'fieldtype': 'Date', 'width': 140},
        {'fieldname': 'delivery_date', 'label': 'Delivery Date', 'fieldtype': 'Date', 'width': 140},
        {'fieldname': 'customer', 'label': 'Customer', 'fieldtype': 'Link', 'width': 130, 'options': 'Customer'},
        {'fieldname': 'customer_name', 'label': 'Customer Name', 'fieldtype': 'Data', 'width': 150},
        {'fieldname': 'customer_group', 'label': 'Customer Group', 'fieldtype': 'Link', 'width': 130, 'options': 'Customer Group'},
        {'fieldname': 'territory', 'label': 'Territory', 'fieldtype': 'Link', 'width': 130, 'options': 'Territory'},
        # {'fieldname': 'project', 'label': 'Project', 'fieldtype': 'Link', 'width': 130, 'options': 'Project'},
        {'fieldname': 'delivered_qty', 'label': 'Delivered Qty', 'fieldtype': 'Float', 'width': 120},
        {'fieldname': 'billed_amount', 'label': 'Billed Amount', 'fieldtype': 'Currency', 'width': 120},
        {'fieldname': 'company', 'label': 'Company', 'fieldtype': 'Link', 'width': 120, 'options': 'Company'}
	]


def get_data():

    sql_query = """
		SELECT
			so.name AS so_name,
			soi.item_code,
			it.item_name,
			soi.item_name AS original_item_name,
			it.item_group,
			it.description,
			soi.qty,
			soi.uom,
			soi.base_rate,
			soi.base_amount,
			so.transaction_date AS so_date,
			soi.delivery_date,
			so.customer,
			cu.customer_name,
			cu.customer_group,
			cu.territory,
			te.parent as territory_parent,
			-- so.project,
			ifnull(soi.delivered_qty, 0) AS delivered_qty,
			ifnull(soi.billed_amt, 0) AS billed_amount,
			so.company
		FROM `tabSales Order Item` soi 
        LEFT JOIN `tabSales Order` so ON so.name = soi.parent 
        LEFT JOIN `tabCustomer` cu ON cu.name = so.customer
		LEFT JOIN `tabItem` it on it.item_code = soi.item_code
		LEFT JOIN `tabTerritory` te on te.name = cu.territory
		WHERE
			so.docstatus = 1
		ORDER BY so.name DESC
	"""

    return frappe.db.sql(sql_query, as_dict=True)
