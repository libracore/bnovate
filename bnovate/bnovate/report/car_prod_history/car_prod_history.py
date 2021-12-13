# Copyright (c) 2021, libracore and contributors
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
        {'fieldname': 'parent', 'fieldtype': 'Link', 'label': _('Parent'), 'options': 'Sales Order', 'width': 100},
        {'fieldname': 'per_delivered', 'fieldtype': 'Percent', 'label': _('Delivered'), 'width': 80},
        {'fieldname': 'customer_name', 'fieldtype': 'Link', 'label': _('Customer'), 'options': 'Customer', 'width': 150},
        {'fieldname': 'qty', 'fieldtype': 'Int', 'label': _('Qty'), 'width': 50}, 
        {'fieldname': 'item_name', 'fieldtype': 'Data ', 'label': _('Item name'), 'width': 300}, 
        {'fieldname': 'delivery_date', 'fieldtype': 'Date', 'label': _('Ship date'), 'width': 80},
        {'fieldname': 'delivered_qty', 'fieldtype': 'Percent', 'label': _('Delivered'), 'width': 50},
        {'fieldname': 'item_code', 'fieldtype': 'Link', 'label': _('Item code'), 'options': 'Item', 'width': 120},
        {'fieldname': 'item_group', 'fieldtype': 'Data', 'label': _('Item group'), 'width': 300},
        {'fieldname': 'status', 'fieldtype': 'Data', 'label': _('Status'), 'width': 100}
    ]
    
def get_data(filters):
    sql_query = """
        SELECT 
            `soi`.`parent` AS `parent`,
            `so`.`per_delivered` AS `per_delivered`,
            `so`.`customer_name` AS `customer_name`,
            `soi`.`qty` AS `qty`, 
            `soi`.`item_name` AS `item_name`, 
            `soi`.`delivery_date` AS `delivery_date`,
            (`soi`.`delivered_qty` / `soi`.`qty` * 100) AS `delivered_qty`,
            `soi`.`item_code` AS `item_code`,
            `soi`.`item_group` AS `item_group`,
            `so`.`status` AS `status`
        FROM `tabSales Order Item` as `soi`
        JOIN `tabSales Order` AS `so` ON `soi`.`parent` = `so`.`name`
        WHERE
            `soi`.`delivery_date` BETWEEN "{from_date}" AND "{to_date}"
            AND `so`.`docstatus` = 1
        ORDER BY `soi`.`delivery_date` ASC;
    """.format(from_date=filters.from_date, to_date=filters.to_date)

    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
