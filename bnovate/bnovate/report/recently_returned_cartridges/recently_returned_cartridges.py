# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.data import add_days, getdate


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {'fieldname': 'name', 'fieldtype': 'Link', 'label': _('Stock Entry'), 'options': 'Stock Entry', 'width': 100},
        {'fieldname': 'posting_date', 'fieldtype': 'Date', 'label': _('Since date'), 'width': 80},
        {'fieldname': 'from_customer', 'fieldtype': 'Link', 'label': _('Customer'), 'options': 'Customer', 'width': 120},
        {'fieldname': 'from_customer_name', 'fieldtype': 'Data', 'label': _('Customer Name'), 'width': 300, 'align': 'left'}, 
        {'fieldname': 'serial_no', 'fieldtype': 'Link', 'label': _('Serial No'), 'options': 'Serial No', 'width': 100},
        {'fieldname': 'open_sales_order', 'fieldtype': 'Link', 'label': _('Sales Order'), 'options': 'Sales Order', 'width': 200, 'align': 'left'},
    ]

def get_data(filters):
    from_date = filters.from_date
    if not from_date:
        from_date = getdate(add_days(None, -30))
    data = frappe.db.sql('''
        SELECT
            ste.name,
            ste.posting_date,
            ste.from_customer,
            ste.from_customer_name,
            sn.serial_no,
            sn.open_sales_order,
            so.docstatus AS open_sales_order_docstatus
        FROM `tabStock Entry Detail` std
        JOIN `tabStock Entry` ste ON ste.name = std.parent
        JOIN `tabSerial No` sn ON sn.serial_no = std.serial_no
        LEFT JOIN `tabSales Order` so ON so.name = sn.open_sales_order
        WHERE std.s_warehouse = "Customer Locations - bN"
            AND std.item_code = "100146"
            AND ste.posting_date >= '{from_date}'
        ORDER BY ste.posting_date DESC
    '''.format(from_date=from_date),
    as_dict=True)

    return data