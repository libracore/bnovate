# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

from operator import attrgetter

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {'fieldname': 'serial_no', 'fieldtype': 'Link', 'label': _('Serial No'), 'options': 'Serial No', 'width': 100},
        {'fieldname': 'type', 'fieldtype': 'Data', 'label': _('Type'), 'width': 150}, 
        {'fieldname': 'status', 'fieldtype': 'Data', 'label': _('Status'), 'width': 150}, 
        {'fieldname': 'location', 'fieldtype': 'Data', 'label': _('Location'), 'width': 150}, 
        # {'fieldname': 'item_code', 'fieldtype': 'Link', 'label': _('Item'), 'options': 'Item', 'width': 100},
        {'fieldname': 'warehouse', 'fieldtype': 'Link', 'label': _('Warehouse'), 'options': 'Warehouse', 'width': 100},
        {'fieldname': 'docname', 'fieldtype': 'Dynamic Link', 'label': _('Transfer doc'), 'options': 'doctype', 'width': 100}, 
        {'fieldname': 'posting_date', 'fieldtype': 'Date', 'label': _('Since date'), 'width': 80},
        {'fieldname': 'owned_by', 'fieldtype': 'Link', 'label': _('Owned by Customer'), 'options': 'Customer', 'width': 120},
        {'fieldname': 'customer_name', 'fieldtype': 'Data', 'label': _('Customer Name'), 'width': 300, 'align': 'left'}, 
        {'fieldname': 'tracking_link', 'fieldtype': 'Data', 'label': _('Tracking No'), 'width': 300, 'align': 'left'}, 
    ]

def get_data(filters):
    extra_filters = ""
    if filters.customer:
        if type(filters.customer) == str:
            filters.customer = [filters.customer]
        customers = '("' + '", "'.join(filters.customer) + '")'
        extra_filters += '\nAND sn.owned_by IN {}'.format(customers)
    
    if filters.only_stored:
        extra_filters += '\nAND sn.warehouse IN ("Repairs - bN", "To Refill - bN", "Finished Goods - bN")'

    if filters.serial_no:
        extra_filters += '\nAND sn.serial_no LIKE "{0}"'.format(filters.serial_no)

    sql_query = """
        SELECT 
            sn.serial_no, 
            IF(sn.serial_no LIKE "%BNO%", "Rental", "Customer-owned") as type,
            NULL as status,
            sn.item_code, 
            sn.warehouse, 
            IF(sn.warehouse = "Customer Locations - bN", "Shipped to Customer", "bNovate") as location,
            sn.purchase_document_type AS doctype,
            sn.purchase_document_no AS docname,
            sn.purchase_date AS posting_date,
            sn.owned_by,
            cr.customer_name,
            dn.carrier,
            dn.tracking_no
        FROM `tabSerial No` sn
        LEFT JOIN `tabStock Entry` ste ON sn.purchase_document_no = ste.name
        LEFT JOIN `tabCustomer` cr ON sn.owned_by = cr.name
        LEFT JOIN `tabDelivery Note` dn ON sn.purchase_document_no = dn.name
        WHERE sn.item_code = "100146"
            AND sn.warehouse IS NOT NULL
            {extra_filters}
        ORDER BY sn.serial_no
    """.format(extra_filters=extra_filters)

    data = frappe.db.sql(sql_query, as_dict=True)

    for row in data:
        if row.warehouse == "Customer Locations - bN":
            row.status = "Shipped"
            row.status_index = 4
        elif row.warehouse == "Repairs - bN":
            row.status = "Refurbishing"
            row.status_index = 1
        elif row.warehouse == "To Refill - bN":
            row.status = "Ready for Refill"
            row.status_index = 2
        elif row.warehouse == "Finished Goods - bN":
            row.status = "Ready to Ship"
            row.status_index = 3

        if row.carrier == "DHL":
            row.tracking_link = '''<a href="https://www.dhl.com/ch-en/home/tracking/tracking-express.html?submit=1&tracking-id={0}" target="_blank">{0}</a>'''.format(row.tracking_no)

        if row['type'] == 'Rental' and row['customer_name']:
            row['type'] = '<span style="color: orangered">{}</span>'.format(row['type'])
            row['customer_name'] = '<span style="color: orangered">{}</span>'.format(row['customer_name'])

    
    data.sort(key=attrgetter('status_index'))
    
    return data
