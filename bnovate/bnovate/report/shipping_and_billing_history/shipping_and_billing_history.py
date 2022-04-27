# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {'fieldname': 'sales_order', 'fieldtype': 'Link', 'label': _('SO'), 'options': 'Sales Order', 'width': 80},
        {'fieldname': 'customer', 'fieldtype': 'Link', 'label': _('Customer'), 'options': 'Customer', 'width': 80},
        {'fieldname': 'customer_name', 'fieldtype': 'Data', 'label': _('Customer Name'), 'width': 150},
        {'fieldname': 'item_code', 'fieldtype': 'Link', 'label': _('Sold item'), 'options': 'Item', 'width': 200},
        {'fieldname': 'sold_rate', 'fieldtype': 'Int', 'label': _('Sold rate'), 'width': 80},
        {'fieldname': 'billed', 'fieldtype': 'Percent', 'label': _('Billed'), 'width': 80},
        {'fieldname': 'delivery_note', 'fieldtype': 'Link', 'label': _('DN'), 'options': 'Delivery Note', 'width': 80},
        {'fieldname': 'shipped_item_code', 'fieldtype': 'Link', 'label': _('Shipped item'), 'options': 'Item', 'width': 200},
        {'fieldname': 'serial_no', 'fieldtype': 'Text', 'label': _('Serial No'), 'width': 150},
        {'fieldname': 'target_warehouse', 'fieldtype': 'Link', 'label': _('Target Warehouse'), 'options': 'Warehouse', 'width': 150},
        {'fieldname': 'ship_date', 'fieldtype': 'Date', 'label': _('Ship date'), 'width': 100},
    ]
    
    
    
def get_data(filters):
    
    sn_filter = ""
    if filters.serial_no:
        sn_filter = """ WHERE di.serial_no LIKE "%{}%" """.format(filters.serial_no)
    sql_query = """
    SELECT       
        /* For each serialized item we deliverd, associate customer name (from SO) and billing percentage (from SO item) */
        so.name as "sales_order",
        so.customer as "customer",
        c.customer_name as "customer_name",
        soi.item_code as "item_code",
        soi.item_name as "item_name",
        soi.rate as sold_rate, /* TODO: figure out currency */
        soi.billed_amt / soi.amount * 100 as "billed",
        di.delivery_note as "delivery_note",
        di.delivered_item_code as "shipped_item_code",
        di.serial_no as "serial_no",
        di.target_warehouse as "target_warehouse",
        dn.posting_date as "ship_date"
    FROM (
    /* delivered_items (DI) subtable: vertical union of packed items and delivery note items, to get delivered serial numbers */
    (
        /* Serial numbers of packed items (for bundles) */
        SELECT
            dni.parent as delivery_note,
            dni.so_detail,
            pi.item_code as delivered_item_code,
            pi.serial_no,
            pi.target_warehouse
        FROM `tabPacked Item` as pi
        JOIN `tabDelivery Note Item` AS dni ON pi.parent_detail_docname = dni.name
        WHERE pi.parenttype = 'Delivery Note' AND pi.serial_no IS NOT NULL AND pi.docstatus = 1
    ) union all (
        /* Serial number of delivery note items (non-bundles) */
        SELECT
            dni.parent as delivery_note,
            dni.so_detail,
            dni.item_code as delivered_item_code,
            dni.serial_no,
            dni.target_warehouse
        FROM `tabDelivery Note Item` as dni
        WHERE dni.serial_no IS NOT NULL AND dni.docstatus = 1
    )) as di
    JOIN `tabSales Order Item` as soi ON soi.name = di.so_detail
    JOIN `tabSales Order` as so ON so.name = soi.parent
    JOIN `tabDelivery Note` as dn on di.delivery_note = dn.name
    JOIN `tabCustomer` as c on so.customer = c.name
    {sn_filter}
    ;
    """.format(from_date=filters.from_date, to_date=filters.to_date, sn_filter=sn_filter)

    data = frappe.db.sql(sql_query, as_dict=True)
    return data
