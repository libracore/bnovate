# Copyright (c) 2025, bnovate, libracore and contributors
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
        {"fieldname": "batch_no", "label": _("Batch"), "fieldtype": "Link", "options": "Batch", "width": 150, "align": "left"},
        {"fieldname": "item_code", "label": _("Item Code"), "fieldtype": "Link", "options": "Item", "width": 180, "align": "left"},
        {"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data", "width": 200},
        {"fieldname": "warehouse", "label": _("Warehouse"), "fieldtype": "Link", "options": "Warehouse", "width": 180},
        {"fieldname": "qty", "label": _("Stock Balance"), "fieldtype": "Float", "width": 120},
        {"fieldname": "stock_uom", "label": _("UOM"), "fieldtype": "Data", "width": 80},
        {"fieldname": "manufacturing_date", "label": _("Manufacturing Date"), "fieldtype": "Date", "width": 130},
        {"fieldname": "expiry_date", "label": _("Expiry Date"), "fieldtype": "Date", "width": 110},
        {"fieldname": "expires_in_days", "label": _("Expires In (Days)"), "fieldtype": "Int", "width": 130},
        {"fieldname": "disabled", "label": _("Disabled"), "fieldtype": "Check", "width": 80, "align": "center"},
    ]

def get_data(filters):

    conditions = ""

    if not filters.status_date:
        filters.status = frappe.utils.nowdate()
    
    if filters.item_code:
        conditions += " AND bs.item_code = '{0}' ".format(filters.item_code)

    if filters.warehouse:
        conditions += " AND bs.warehouse = '{0}' ".format(filters.warehouse)

    if filters.only_in_stock:
        conditions += " AND qty > 0 "

    if filters.expires_in_days:
        conditions += " AND DATEDIFF(b.expiry_date, CURDATE()) <= {0} ".format(filters.expires_in_days)

    # Aggregate actual_qty from Stock Ledger Entry per batch and warehouse
    query = """
WITH batchwise_stock AS (
  SELECT
   -- sle.posting_date,
   sle.item_code,
   sle.batch_no,
   sle.warehouse,
   SUM(sle.actual_qty) as qty,
   sle.stock_uom
  FROM `tabStock Ledger Entry` sle
  WHERE batch_no IS NOT NULL AND batch_no <> ''
    AND sle.posting_date <= '{status_date}'
  GROUP BY batch_no, warehouse
)

SELECT
  bs.*,
  it.item_name,
  b.manufacturing_date,
  b.expiry_date,
  b.disabled,
  DATEDIFF(b.expiry_date, CURDATE()) as expires_in_days
FROM batchwise_stock bs
JOIN `tabItem` it on it.item_code = bs.item_code
JOIN `tabBatch` b on b.batch_id = bs.batch_no
WHERE TRUE {conditions}
    """.format(conditions=conditions, status_date=filters.status_date)

    # run query
    data = frappe.db.sql(query, as_dict=1)


    return data
