# Copyright (c) 2013-2020, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link",  "options": "Warehouse", "width": 150},
        #{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data",  "width": 100},
        #{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group",  "width": 120},
        {"label": _("Quantity"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {"label": _("Value"), "fieldname": "value", "fieldtype": "Currency", "width": 100},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]

def get_data(filters):
    # get all item/warehouse combinations
    item_warehouse_query = """SELECT DISTINCT(CONCAT(`item_code`, "::", `warehouse`)) AS `key`, 
          `item_code`, `warehouse`
        FROM `tabStock Ledger Entry`;"""
    item_warehouses = frappe.db.sql(item_warehouse_query, as_dict=True)
    
    # prepare target list
    stock_levels = []
    
    for item_warehouse in item_warehouses:
        # get stock level per warehouse based on last level from stock ledger
        sql_query = """SELECT `qty_after_transaction` AS `qty`, 
                            `stock_value` AS `value`
                       FROM `tabStock Ledger Entry` AS `sle1`
                       WHERE `sle1`.`item_code` = '{item_code}'
                           AND `sle1`.`posting_date` <= NOW()
                           AND `sle1`.`warehouse` LIKE '{warehouse}'
                       ORDER BY `posting_date` DESC, `posting_time` DESC
                       LIMIT 1;""".format(item_code=item_warehouse['item_code'], 
                                          warehouse=item_warehouse['warehouse'])
        stock_level = frappe.db.sql(sql_query, as_dict=True)

        if stock_level[0]['qty'] > 0 or stock_level[0]['value'] > 0:
            stock_levels.append({
                'item_code': item_warehouse['item_code'],
                'warehouse': item_warehouse['warehouse'],
                'qty': stock_level[0]['qty'],
                'value': stock_level[0]['value']
            })
        
    return stock_levels
