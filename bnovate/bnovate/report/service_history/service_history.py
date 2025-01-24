# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
    return get_columns(), get_data(filters)

def get_columns():
    return [
        {'fieldname': 'report', 'fieldtype': 'Link', 'label': 'Service Report', 'options': 'Service Report', 'width': 80},
        {'fieldname': 'customer', 'fieldtype': 'Link', 'label': 'Customer', 'options': 'Customer', 'width': 80},
        {'fieldname': 'customer_name', 'fieldtype': 'Data', 'label': 'Customer Name', 'width': 150},
        {'fieldname': 'intervention_date', 'fieldtype': 'Date', 'label': 'Intervention Date', 'width': 120},
        {'fieldname': 'serial_no', 'fieldtype': 'Link', 'options': 'Serial No', 'label': 'Serial No', 'width': 100},
         {'fieldname': 'item_code', 'fieldtype': 'Link', 'label': 'Item Code', 'options': 'Item', 'width': 80},
        {'fieldname': 'item_name', 'fieldtype': 'Data', 'label': 'Item Name', 'width': 150},
        {'fieldname': 'reason_for_visit', 'fieldtype': 'Data', 'label': 'Reason for visit', 'width': 120},
        {'fieldname': 'channel', 'fieldtype': 'Data', 'label': 'Channel', 'width': 100},
        {'fieldname': 'technician_name', 'fieldtype': 'Data', 'label': 'Technician Name', 'width': 150},

    ]

def get_data(filters):
    docstatus_filter = 'sr.docstatus = 1'
    if filters.include_drafts:
        docstatus_filter = 'sr.docstatus <= 1'

    customer_filter = ''
    if filters.customer:
        customer_filter = 'AND sr.customer = "{}"'.format(filters.customer)

    serial_no_filter = ''
    if filters.serial_no:
        serial_no_filter = 'AND sr.serial_no = "{}"'.format(filters.serial_no)
        
    sql_query = """
SELECT
    sr.name as report,
    sr.customer,
    cu.customer_name,
    sr.intervention_date,

    sr.serial_no,
    it.item_code,
    it.item_name,

    sr.reason_for_visit,

    sr.channel,
    IFNULL(sr.bnovate_technician_name, sr.technician_name) AS technician_name

FROM `tabService Report` sr
JOIN `tabCustomer` cu ON cu.name = sr.customer
JOIN `tabSerial No` sn ON sn.name = sr.serial_no
JOIN `tabItem` it on it.item_code = sn.item_code
WHERE {docstatus_filter}
    {customer_filter}
    {serial_no_filter}
ORDER BY sr.intervention_date DESC
    """.format(docstatus_filter=docstatus_filter, customer_filter=customer_filter, serial_no_filter=serial_no_filter)
    data = frappe.db.sql(sql_query, as_dict=True)
    return data
