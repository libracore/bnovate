# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date, timedelta
from bnovate.bnovate.utils.iot_apis import combase_get_cycle_usage

class ConnectivityUsage(Document):
	pass


@frappe.whitelist()
def fetch_usage_for_period(start_date, end_date=None):
	""" Fetch usage from cell provider and save to DB

	Billing periods are months. Fetch all months up to either last month or 
	the month containing end_date, whichever is earlier.

	"""
	if type(start_date) != date:
		start_date = frappe.utils.dateutils.get_datetime(start_date).date()

	# Fetch up until last month - current cycle shouldn't be saved to DB
	today = date.today()
	if end_date is None or end_date > today:
		end_date = first_day_of_prev_month(today)
	elif end_date.year == today.year and end_date.month == today.month:
		end_date = first_day_of_prev_month(today)
	start_date = first_day_of_month(start_date)

	# Build range of billing cycles to fetch.
	# To avoid duplicates, do not fetch if it already exists in DB:
	cycles = []
	while start_date <= end_date:
		exists = frappe.get_all("Connectivity Usage", filters={
			'period_start': ['=', start_date]
		})
		if not exists:
			cycles.append(start_date)
		start_date = first_day_of_next_month(start_date)

	cp_lookup = { cp['iccid']: cp for cp in frappe.get_all("Connectivity Package", fields=['name', 'iccid', 'customer'])}

	usage = combase_get_cycle_usage(cycles)
	for cycle_start, device_usages in usage.items():
		for device_id, device_usage in device_usages.items():
			cp = cp_lookup[device_id] if device_id in cp_lookup else None
			new_entry = frappe.get_doc({
				'doctype': 'Connectivity Usage',
				'iccid': device_id,
				'period_start': cycle_start,
				'period_end': last_day_of_month(cycle_start),
				'data_usage': device_usage,
				'connectivity_package': cp['name'] if cp else None,
				'customer': cp['customer'] if cp else None,
				'docstatus': 1,
			})
			new_entry.insert()

	frappe.db.commit()

def fetch_usage_last_few_months():
	""" Called by hooks.py on a periodic basis """
	return fetch_usage_for_period(date.today() - timedelta(days=3*31))


#####################################
# Helpers
#####################################

def first_day_of_month(day: date):
	return day.replace(day=1)

def first_day_of_prev_month(day: date):
	return first_day_of_month(day.replace(day=1) - timedelta(days=1))

def first_day_of_next_month(day: date):
	return first_day_of_month(day.replace(day=28) + timedelta(days=4))

def last_day_of_month(day: date):
	return first_day_of_next_month(day) - timedelta(days=1)


