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
		query_filters += "AND w.year = YEAR(CURDATE())"
	sql_query = """

WITH so AS ( -- Data from SO
  SELECT
    so.name,
    so.company,
    so.transaction_date,
    YEAR(so.transaction_date) as year,
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

scp AS ( -- scp: Subscription Contract Period

  WITH RECURSIVE bp AS ( -- bp: billing periods
    SELECT
        ss.name,
        ss.company,
        ssi.name AS ssi_docname,
        ssi.idx AS ssi_index,
        start_date,
        -- Continue at most until end of current month / filter end date month. For yearly we still generate an invoice for entire year 
        LEAST(IFNULL(ss.end_date, '2099-12-31'), CURDATE()) AS end_date,
        ss.interval,
        start_date as period_start,
        CASE ss.interval
            WHEN 'Yearly' THEN DATE_ADD(DATE_ADD(start_date, INTERVAL 1 YEAR), INTERVAL -1 DAY)
            WHEN 'Monthly' THEN DATE_ADD(DATE_ADD(start_date, INTERVAL 1 MONTH), INTERVAL -1 DAY)
        END AS period_end
    FROM `tabSubscription Contract Item` ssi
    JOIN `tabSubscription Contract` ss on ssi.parent = ss.name
    WHERE ss.company = "{company}"
      AND ss.docstatus = 1
    UNION ALL
    SELECT
        name,
        company,
        ssi_docname,
        ssi_index,
        start_date,
        end_date,
        bp.interval,
        CASE bp.interval
            WHEN 'Yearly' THEN DATE_ADD(period_start, INTERVAL 1 YEAR) 
            WHEN 'Monthly' THEN DATE_ADD(period_start, INTERVAL 1 MONTH)
        END AS period_start,
        CASE bp.interval
            -- period_start is previous iteration -> add two intervals
            WHEN 'Yearly' THEN DATE_ADD(DATE_ADD(period_start, INTERVAL 2 YEAR), INTERVAL -1 DAY)
            WHEN 'Monthly' THEN DATE_ADD(DATE_ADD(period_start, INTERVAL 2 MONTH), INTERVAL -1 DAY)
        END AS period_end
    FROM bp
    WHERE period_end < end_date -- note this is period_end from previous iteration!
  )
  SELECT
      bp.name,
      bp.company,
      bp.period_start as transaction_date,
      YEAR(bp.period_start) as year,
      DATE_ADD(bp.period_start, INTERVAL(-WEEKDAY(bp.period_start)) DAY) as week_start,
      ssi.qty,
      ssi.item_code,
      ssi.item_name,
      ssi.base_net_amount,
      "Service" as item_group,
      "Service" as item_supergroup
  FROM bp
  JOIN `tabSubscription Contract Item` ssi ON ssi.name = bp.ssi_docname
  ORDER BY period_start DESC, name
),
agg as ( -- combine Sales Orders and Subscription Contracts
  SELECT 
    *,
    WEEK(so.week_start) as week_num
	FROM so
  UNION ALL
  SELECT 
    *,
    WEEK(scp.week_start) as week_num
	FROM scp
),
w as ( -- weekdata, sums grouped by week
  SELECT
    agg.year,
    agg.week_start,
    agg.week_num,
  	agg.transaction_date,
    SUM(CASE WHEN agg.item_group = "Instruments" THEN agg.qty ELSE 0 END) as instrument_qty,
    SUM(CASE WHEN agg.item_supergroup = "Instruments & Fills" THEN agg.base_net_amount ELSE 0 END) as instrument_amount,
    SUM(CASE WHEN agg.item_supergroup = "Refills" THEN agg.base_net_amount ELSE 0 END) as cartridge_amount,
    SUM(CASE WHEN agg.item_supergroup = "Service" THEN agg.base_net_amount ELSE 0 END) as service_amount,
    SUM(CASE WHEN agg.item_supergroup IN ("Instruments & Fills", "Refills", "Service") THEN agg.base_net_amount ELSE 0 END) as total_amount,
    SUM(CASE WHEN agg.item_supergroup = "Other" THEN agg.base_net_amount ELSE 0 END) as other_amount
  FROM agg
  GROUP BY agg.year, agg.week_num
  ORDER BY agg.transaction_date DESC
)

-- Here we can apply cumsums
SELECT
	*,
	SUM(w.instrument_qty) OVER (PARTITION BY w.year ORDER BY w.transaction_date) AS instrument_qty_cum,
	SUM(w.total_amount) OVER (PARTITION BY w.year ORDER BY w.transaction_date) AS total_amount_cum
FROM w
WHERE w.week_start < CURDATE()
  {query_filters}
ORDER BY w.transaction_date DESC
	""".format(company=filters.company, query_filters=query_filters)

	return frappe.db.sql(sql_query, as_dict=True)