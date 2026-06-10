# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe


def execute(filters=None):
    columns, data = [], []
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {
            "label": "Line No",
            "fieldname": "idx",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "label": "Agr,ment",
            "fieldname": "agreement",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": "Invoice Number",
            "fieldname": "dn_name",
            "fieldtype": "Link",
            "options": "Delivery Note",
            "width": 150
        },
        {
            "label": "Invoice Date",
            "fieldname": "posting_date",
            "fieldtype": "Data",
            "width": 120

        },
        {
            "label": "Code Client",
            "fieldname": "customer_number",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": "Total Gross Weight",
            "fieldname": "total_gross_weight",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "Total Net Weight",
            "fieldname": "total_net_weight",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "EORI",
            "fieldname": "eori_number",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Recipient's VAT Number",
            "fieldname": "tax_id",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Item Name",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Customs Tariff Number",
            "fieldname": "customs_tariff_number",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Net Weight",
            "fieldname": "total_weight",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "Origin",
            "fieldname": "country_of_origin",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Preferential Origin",
            "fieldname": "preferential_origin",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Quantity Per Item",
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "Items Value",
            "fieldname": "amount",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "Currency",
            "fieldname": "currency",
            "fieldtype": "Data",
            "width": 80
        },
        {
            "label": "AWB Number",
            "fieldname": "master_awb_number",
            "fieldtype": "Data",
            "width": 150
        }
    ]


def get_data(filters):

    date_filter = ""
    if filters and filters.date:
        date_filter = "AND dn.posting_date = '{date}'".format(date=filters.date)

    query = """
    WITH breakbulk_totals AS (
        SELECT
           dn.name as dn_name, 
           SUM((SELECT COALESCE(SUM(weight), 0) FROM `tabShipment Parcel` WHERE parent = dn.name)) AS gross_weight,
           SUM(dn.total_net_weight) AS net_weight,
           dn.breakbulk_master_no
        FROM `tabDelivery Note` dn
        WHERE TRUE {date_filter}
        GROUP BY dn.breakbulk_master_no
    )

    SELECT
        dni.idx,
        "S." as agreement,
        dni.parent as dn_name,
        dni.item_name,
        DATE_FORMAT(dn.posting_date, '%Y%m%d') as posting_date,
        "xxx" as customer_number,
        dni.customs_tariff_number,
        dni.country_of_origin,
        bt.gross_weight AS total_gross_weight,
        bt.net_weight AS total_net_weight,
        dn.eori_number,
        REGEXP_REPLACE(dn.tax_id, '[^a-zA-Z0-9]', '') as tax_id,
        dni.total_weight,
        "NO" as preferential_origin,
        dni.qty,
        dni.amount,
        dn.currency,
        dn.breakbulk_master_no as master_awb_number
    FROM `tabDelivery Note Item` dni
    LEFT JOIN `tabDelivery Note` dn ON dni.parent = dn.name
    LEFT JOIN breakbulk_totals bt ON bt.breakbulk_master_no = dn.breakbulk_master_no
    WHERE dn.docstatus != 2
        {date_filter}
        AND dn.breakbulk_master_no IS NOT NULL AND TRIM(dn.breakbulk_master_no) != ''
    ORDER BY dn.name, dni.idx
    """.format(date_filter=date_filter)
    return frappe.db.sql(query, as_dict=1)
