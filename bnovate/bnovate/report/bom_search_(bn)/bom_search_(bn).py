# Copyright (c) 2025, bNovate, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json

from six import iteritems

def execute(filters=None):

    return get_columns(), get_data(filters)


def get_columns():
    return [
        {
            "fieldname": "name",
            "label": "BOM",
            "width": 200,
            "fieldtype": "Link",
            "options": "BOM"
        },
        {
            "fieldname": "item",
            "label": "Output Item Code",
            "width": 250,
            "fieldtype": "Link",
            "options": "Item"
        },
        # {
        #     "fieldname": "item_name",
        #     "label": "Item Name",
        #     "width": 180,
        #     "fieldtype": "Data"
        # },
        {
            "fieldname": "bom_description",
            "label": "BOM Description",
            "width": 200,
            "fieldtype": "Data",
            "align": "left"
        },
        {
            "fieldname": "item_qty",
            "label": "Input Qty",
            "width": 100,
            "fieldtype": "Float"
        },
        {
            "fieldname": "bom_qty",
            "label": "Output Qty",
            "width": 100,
            "fieldtype": "Float"
        },
        {
            "fieldname": "is_active",
            "label": "Is Active?",
            "width": 50,
            "fieldtype": "Check"
        },
        {
            "fieldname": "is_default",
            "label": "Is Default?",
            "width": 50,
            "fieldtype": "Check"
        },
    ]	

def get_data(filters):
    doctype = "BOM Explosion Item" if filters.search_sub_assemblies else "BOM Item"

    additional_filters = ""
    if filters.only_active:
        additional_filters += " AND bom.is_active = 1"
    if filters.only_default:
        additional_filters += " AND bom.is_default = 1"

    query = """
    SELECT
        bom.name,
        bom.item,
        bom.item_name,
        bom.bom_description,
        bom.is_active,
        bom.is_default,
        bom.quantity AS bom_qty,
        bi.qty AS item_qty
    FROM `tab{doctype}` bi
    JOIN `tabBOM` bom ON bom.name = bi.parent
    WHERE bi.item_code = "{item1}"
        {additional_filters}
    """.format(doctype=doctype, item1=filters.item1, additional_filters=additional_filters)

    return frappe.db.sql(query, as_dict=1)
 
     