# Copyright (c) 2022, bNovate, libracore and contributors
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
        {'fieldname': 'purchase_order', 'fieldtype': 'Link', 'label': _('PO'), 'options': 'Purchase Order', 'width': 80},
        {'fieldname': 'supplier', 'fieldtype': 'Link', 'label': _('Supplier'), 'options': 'Supplier', 'width': 80},
        {'fieldname': 'supplier_name', 'fieldtype': 'Data', 'label': _('Supplier Name'), 'width': 200, 'align': 'left'},
        {'fieldname': 'expected_delivery_date', 'fieldtype': 'Date', 'label': _('Expected date'), 'width': 80},
        {'fieldname': 'item_code', 'fieldtype': 'Link', 'label': _('Sold item'), 'options': 'Item', 'width': 200, 'align': 'left'},
        {'fieldname': 'qty', 'fieldtype': 'Int', 'label': _('Qty total'), 'width': 100}, 
        {'fieldname': 'remaining_qty', 'fieldtype': 'Int', 'label': _('Qty to Receive'), 'width': 100},
        {'fieldname': 'bnovate_person', 'fieldtype': 'Data', 'label': _('bNovate Contact'), 'width': 200},
    ]
      
    
def get_data(filters):
    extra_filters = ""
    if filters.bnovate_contact:
        extra_filters += "AND po.bnovate_person = '{}'\n".format(filters.bnovate_contact)
    if filters.only_stock_items:
        extra_filters += "AND it.is_stock_item = {}\n".format(filters.only_stock_items)

    days_from_now = filters.days_from_now or 0

    sql_query = """
SELECT 
    po.name as purchase_order,
    po.supplier,
    s.supplier_name as supplier_name,
    poi.item_code, 
    poi.item_name,
    poi.description,
    poi.qty, 
    (poi.qty - poi.received_qty) as remaining_qty,
    IFNULL(poi.expected_delivery_date, poi.schedule_date) as expected_delivery_date,
    po.bnovate_person
FROM `tabPurchase Order` as po
    JOIN `tabPurchase Order Item` as poi ON po.name = poi.parent
    JOIN `tabItem` as it ON poi.item_code = it.name
    JOIN `tabSupplier` as s ON po.supplier = s.name
WHERE poi.received_qty < poi.qty
    AND IFNULL(poi.expected_delivery_date, poi.schedule_date) <= DATE_ADD(CURRENT_DATE(), INTERVAL {days_from_now} DAY)
    AND po.docstatus = 1
    AND po.status != 'Closed'
    {extra_filters}
ORDER BY IFNULL(poi.expected_delivery_date, poi.schedule_date) DESC
    ;
    """.format(extra_filters=extra_filters, days_from_now=days_from_now)

    data = frappe.db.sql(sql_query, as_dict=True)
    return data
