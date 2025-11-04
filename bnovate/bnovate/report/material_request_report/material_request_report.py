# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
    return get_columns(), get_data(filters)

def get_columns():
    """
    Column definitions extracted from the SQL SELECT aliases.
    """
    return [
        {"fieldname": "material_request", "label": "Material Request", "fieldtype": "Link", "options": "Material Request", "width": 120},
        {"fieldname": "request_type", "label": "Request Type", "fieldtype": "Data", "width": 120},
        {"fieldname": "transaction_date", "label": "Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "item_code", "label": "Item Code", "fieldtype": "Link", "options": "Item", "width": 220, "align": "left"},
        {"fieldname": "qty", "label": "Qty", "fieldtype": "Float", "width": 100},
        {"fieldname": "uom", "label": "UOM", "fieldtype": "Link", "options": "UOM", "width": 100},
        {"fieldname": "ordered_qty", "label": "Ordered Qty", "fieldtype": "Float", "width": 100},
        {"fieldname": "qty_to_order", "label": "Qty to Order", "fieldtype": "Float", "width": 100},
        {"fieldname": "description", "label": "Description", "fieldtype": "Data", "width": 200},
        {"fieldname": "supplier", "label": "Default Supplier", "fieldtype": "Link", "options": "Supplier", "width": 140},
        {"fieldname": "supplier_name", "label": "Supplier Name", "fieldtype": "Data", "width": 180},
        {"fieldname": "item_group", "label": "Item Group", "fieldtype": "Link", "options": "Item Group", "width": 140}, 
        {"fieldname": "assigned_to", "label": "Assigned To", "fieldtype": "Link", "options": "User", "width": 140},
        {"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company", "width": 140},
    ]

def get_data(filters):

    conditions = ""

    if filters.only_unassigned:
        conditions += " AND (mr_item.assigned_to IS NULL OR mr_item.assigned_to = '') "

    if filters.item_group:
        conditions += " AND mr_item.item_group = {0} ".format(frappe.db.escape(filters.item_group))

    if filters.request_type:
        conditions += " AND mr.material_request_type = {0} ".format(frappe.db.escape(filters.request_type))

    query = """
SELECT 
    mr.name AS material_request,
    mr.material_request_type AS request_type,
    mr.transaction_date AS transaction_date,
    mr_item.name AS mr_item,
    mr_item.item_code AS item_code,
    SUM(IFNULL(mr_item.stock_qty, 0)) AS qty,
    IFNULL(mr_item.stock_uom, '') AS uom,
    SUM(IFNULL(mr_item.ordered_qty, 0)) AS ordered_qty, 
    (SUM(mr_item.stock_qty) - SUM(IFNULL(mr_item.ordered_qty, 0))) AS qty_to_order,
    mr_item.item_name AS item_name,
    mr_item.description AS description,
    item_default.default_supplier AS supplier,
    supplier.supplier_name AS supplier_name,
    mr_item.item_group AS item_group,
    mr_item.assigned_to AS assigned_to,
    mr.company AS company
FROM
    `tabMaterial Request` mr
JOIN `tabMaterial Request Item` mr_item ON mr_item.parent = mr.name
JOIN `tabItem Default` item_default ON item_default.parent = mr_item.item_code AND item_default.company = mr.company
JOIN `tabSupplier` supplier ON supplier.name = item_default.default_supplier
WHERE
    mr.material_request_type = "Purchase"
    AND mr.docstatus = 1
    AND mr.status != "Stopped"
    {conditions}
GROUP BY mr.name, mr_item.item_code
HAVING
    SUM(IFNULL(mr_item.ordered_qty, 0)) < SUM(IFNULL(mr_item.stock_qty, 0))
ORDER BY mr.transaction_date ASC
    """.format(conditions=conditions)

    return frappe.db.sql(query, as_dict=1)