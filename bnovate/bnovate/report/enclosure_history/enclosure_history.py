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
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Time"), "fieldname": "time", "fieldtype": "Data", "width": 100},
        {"label": _("Document"), "fieldname": "document", "fieldtype": "Data", "width": 80},
        {"label": _("Stock Entry"), "fieldname": "stock_entry", "fieldtype": "Link",  "options": "Stock Entry", "width": 100},
        {"label": _("Delivery Note"), "fieldname": "delivery_note", "fieldtype": "Link",  "options": "Delivery Note", "width": 100},
        {"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 150},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 100},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]

def get_data(filters):
    if not filters.snr:
        return None
    # get all item/warehouse combinations
    sql_query = """SELECT 
          `document`,
          `stock_entry`,
          `delivery_note`,
          `snr`,
          `date`,
          `time`,
          `type`,
          `warehouse`
        FROM (SELECT *
        FROM (SELECT
          `tabStock Entry`.`name` AS `document`,
          `tabStock Entry`.`name` AS `stock_entry`,
          "" AS `delivery_note`,
          `tabStock Entry Detail`.`serial_no` AS `snr`,
          `tabStock Entry`.`posting_date` AS `date`,
          `tabStock Entry`.`posting_time` AS `time`,
          `tabStock Entry`.`stock_entry_type` AS `type`,
          `tabStock Entry Detail`.`t_warehouse` As `warehouse`
        FROM `tabStock Entry Detail`
        LEFT JOIN `tabStock Entry` ON `tabStock Entry`.`name` = `tabStock Entry Detail`.`parent`
        WHERE `serial_no` LIKE "%{snr}%"
          AND `tabStock Entry`.`docstatus` = 1
        GROUP BY `tabStock Entry`.`name`
        ORDER BY `tabStock Entry`.`posting_date` DESC, `tabStock Entry`.`posting_time` DESC, `tabStock Entry Detail`.`idx` DESC) AS `se`
        UNION SELECT
          `tabDelivery Note`.`name` AS `document`,
          "" AS `stock_entry`,
          `tabDelivery Note`.`name` AS `delivery_note`,
          `tabDelivery Note Item`.`serial_no` AS `snr`,
          `tabDelivery Note`.`posting_date` AS `date`,
          `tabDelivery Note`.`posting_time` AS `time`,
          "Delivery Note" AS `type`,
          `tabDelivery Note Item`.`target_warehouse` AS `warehouse`
        FROM `tabDelivery Note Item`
        LEFT JOIN `tabDelivery Note` ON `tabDelivery Note`.`name` = `tabDelivery Note Item`.`parent`
        WHERE `tabDelivery Note Item`.`serial_no` LIKE "%{snr}%"
          AND `tabDelivery Note`.`docstatus` = 1
        ) AS `raw`
        ORDER BY `raw`.`date` DESC, `raw`.`time` DESC;""".format(snr=filters.snr)
    history = frappe.db.sql(sql_query, as_dict=True)
        
    return history
