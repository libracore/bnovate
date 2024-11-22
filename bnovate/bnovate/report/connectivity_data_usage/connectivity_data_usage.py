# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from datetime import date

import frappe
from frappe import _

from bnovate.bnovate.doctype.connectivity_usage.connectivity_usage import last_day_of_month

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	if filters.summarize:
		return [
			{'fieldname': 'period_start', 'label': _('Period Start '), 'fieldtype': 'Date', 'width': 80},
			{'fieldname': 'period_end', 'label': _('Period End'), 'fieldtype': 'Date', 'width': 80},

			{'fieldname': 'sum_usage', 'fieldtype': 'Number', 'label': _('SUM Usage [MB]'), 'width': 150}, 
			{'fieldname': 'avg_usage', 'fieldtype': 'Number', 'label': _('MEAN Usage [MB]'), 'width': 150}, 
			{'fieldname': 'max_usage', 'fieldtype': 'Number', 'label': _('MAX Usage [MB]'), 'width': 150}, 
		]
	else:
		return [
			{'fieldname': 'period_start', 'label': _('Period Start '), 'fieldtype': 'Date', 'width': 80},
			{'fieldname': 'period_end', 'label': _('Period End'), 'fieldtype': 'Date', 'width': 80},

			{'fieldname': 'connectivity_package', 'fieldtype': 'Link', 'label': _('Connectivity Package'), 'options': 'Connectivity Package', 'width': 100},

			{'fieldname': 'customer', 'fieldtype': 'Link', 'label': _('Customer'), 'options': 'customer', 'width': 100},
			{'fieldname': 'customer_name', 'fieldtype': 'data', 'label': _('Customer Name'), 'options': 'customer_name', 'width': 200},

			{'fieldname': 'data_usage', 'fieldtype': 'Number', 'label': _('Data Usage [MB]'), 'width': 150}, 
		]


def get_data(filters):
	start_date = filters.start_date if filters.start_date is not None else ""
	end_date = filters.end_date if filters.end_date is not None else last_day_of_month(date.today())

	extra_filters = ""
	if filters.customer:
		extra_filters += 'AND cu.customer LIKE "{}"'.format(filters.customer)
	if filters.connectivity_package:
		extra_filters += 'AND cu.connectivity_package LIKE "{}"'.format(filters.connectivity_package)

	if filters.summarize:
		sql_query = """
		SELECT
			cu.period_start,
			cu.period_end,
			ROUND(SUM(cu.data_usage)) as sum_usage,
			ROUND(AVG(cu.data_usage)) as avg_usage,
			ROUND(MAX(cu.data_usage)) as max_usage
		FROM `tabConnectivity Usage` cu
		JOIN `tabConnectivity Package` cp ON cu.connectivity_package = cp.name
		WHERE cu.period_start >= "{start_date}"
			AND cu.period_end <= "{end_date}"
			{extra_filters}
		GROUP BY cu.period_start
		ORDER BY cu.period_start, cu.data_usage DESC
		""".format(start_date=start_date, end_date=end_date, extra_filters=extra_filters)
	else:
		sql_query = """
		SELECT
			cu.period_start,
			cu.period_end,
			cu.connectivity_package,
			ROUND(cu.data_usage) as data_usage,
			cp.customer,
			cp.customer_name
		FROM `tabConnectivity Usage` cu
		JOIN `tabConnectivity Package` cp ON cu.connectivity_package = cp.name
		WHERE cu.period_start >= "{start_date}"
			AND cu.period_end <= "{end_date}"
			{extra_filters}
		ORDER BY cu.period_start, cu.data_usage DESC
		""".format(start_date=start_date, end_date=end_date, extra_filters=extra_filters)

	return frappe.db.sql(sql_query, as_dict=True)