# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext import get_company_currency, get_default_company

def execute(filters=None):
	if filters.company is None:
		filters.company = get_default_company()

	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters=None):
	currency = get_company_currency(filters.company)
	return [
		{"label": _("Week"), "fieldname": "week_num", "fieldtype": "Data", "width": 50},
        {"label": _("Start"), "fieldname": "week_start", "fieldtype": "Date", "width": 80},
        {"label": _("Instrument Qty"), "fieldname": "instrument_qty", "fieldtype": "Int", "width": 120},
        {"label": _("Instrument Qty YTD"), "fieldname": "instrument_qty_cum", "fieldtype": "Int", "width": 150},
        {"label": _("Instruments & Cartridges {0}".format(currency)), "fieldname": "instrument_amount", "fieldtype": "Currency", "width": 200},
        {"label": _("Refills {0}".format(currency)), "fieldname": "cartridge_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Service {0}".format(currency)), "fieldname": "service_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Total {0}".format(currency)), "fieldname": "total_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Total {0} YTD".format(currency)), "fieldname": "total_amount_cum", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters=None):
	query_filters = ""
	if filters.only_current_fy:
		query_filters += "WHERE w.year = YEAR(CURDATE())"
	sql_query = """

WITH so AS ( -- Data from SO
  SELECT
    so.name,
    so.company,
    so.transaction_date,
    YEAR(so.transaction_date) as year,
    WEEK(so.transaction_date) as week_num,
    DATE_ADD(so.transaction_date, INTERVAL(-WEEKDAY(so.transaction_date)) DAY) as week_start,
    soi.qty,
    soi.item_code,
    it.item_name,
    soi.base_net_amount,
    it.item_group,
    CASE
  		WHEN soi.item_group IN ("Instruments", "New Cartridges") THEN "Instruments & Fills"
      WHEN soi.item_group IN ("Spare Parts", "Service and Support Interventions", "Generic Services", "Accessories", "Packaging") THEN "Service"
      WHEN soi.item_group IN ("Cartridge Refills") THEN "Refills"
      ELSE "Other" -- Warning: this include transfers to subcontractors!
    END as item_supergroup
  FROM `tabSales Order Item` soi
  JOIN `tabSales Order` so on soi.parent = so.name
  JOIN `tabItem` it on soi.item_code = it.name
  WHERE so.company = "{company}"
    AND so.docstatus = 1
  ORDER BY so.transaction_date DESC
),
w as ( -- weekdata, sums grouped by week
  SELECT
    so.year,
    so.week_start,
    so.week_num,
  	so.transaction_date,
    SUM(CASE WHEN so.item_group = "Instruments" THEN so.qty ELSE 0 END) as instrument_qty,
    SUM(CASE WHEN so.item_supergroup = "Instruments & Fills" THEN so.base_net_amount ELSE 0 END) as instrument_amount,
    SUM(CASE WHEN so.item_supergroup = "Refills" THEN so.base_net_amount ELSE 0 END) as cartridge_amount,
    SUM(CASE WHEN so.item_supergroup = "Service" THEN so.base_net_amount ELSE 0 END) as service_amount,
    SUM(CASE WHEN so.item_supergroup IN ("Instruments & Fills", "Refills", "Service") THEN so.base_net_amount ELSE 0 END) as total_amount,
    SUM(CASE WHEN so.item_supergroup = "Other" THEN so.base_net_amount ELSE 0 END) as other_amount
  FROM so
  GROUP BY so.year, so.week_num
  ORDER BY so.transaction_date DESC
)

-- Here we can apply cumsums
SELECT
	*,
	SUM(w.instrument_qty) OVER (PARTITION BY w.year ORDER BY w.transaction_date) AS instrument_qty_cum,
	SUM(w.total_amount) OVER (PARTITION BY w.year ORDER BY w.transaction_date) AS total_amount_cum
FROM w
{query_filters}
ORDER BY w.transaction_date DESC
	""".format(company=filters.company, query_filters=query_filters)

	return frappe.db.sql(sql_query, as_dict=True)