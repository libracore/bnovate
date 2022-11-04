# Copyright (c) 2022, bnovate, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from contextlib import nullcontext
import frappe
from frappe import _

from urllib.parse import quote

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{'fieldname': 'item_code', 'fieldtype': 'Link', 'options': 'Item', 'label': _('Item'), 'width': 400},
		# {'fieldname': 'item_name', 'fieldtype': 'Data', 'label': _('Item Name'), 'width': 300},
		{'fieldname': 'batch_no', 'fieldtype': 'Link', 'options': 'Batch', 'label': _('Batch'), 'width': 150},
		{'fieldname': 'serial_no', 'fieldtype': 'Link', 'options': 'Serial No', 'label': _('Serial No'), 'width': 150},
		{'fieldname': 'production_date', 'fieldtype': 'Date', 'label': _('Date'), 'width': 100},
		{'fieldname': 'voucher_type', 'fieldtype': 'Data', 'label': _('Voucher Type'), 'width': 100},
		{'fieldname': 'voucher_no', 'fieldtype': 'Data', 'label': _('Voucher'), 'width': 100},
	]

name_memo = {}
def get_name(item_code):
	if item_code in name_memo:
		return name_memo[item_code]

	item = frappe.get_doc('Item', item_code)
	name_memo[item_code] = item.item_name
	return item.item_name

def build_tree(data, indent=0, batch_no=None, serial_no=None, visited_nodes={}):

	print("looking for batch no or serial no", batch_no, serial_no)

	if not batch_no and not serial_no:
		# Ignore items with no serial or batch no.
		return

	filters={
		'actual_qty': ['>', '0'],
		'voucher_type': ['in', ['Stock Entry', 'Purchase Receipt']],
	}
	if batch_no:
		filters['batch_no'] = batch_no
	else:
		filters['serial_no'] = serial_no

	# Find the stock entry that created that batch or SN
	ledger_entries = frappe.get_all('Stock Ledger Entry', 
		filters=filters, 
		fields=['item_code', 'actual_qty', 'voucher_no', 'voucher_type', 'batch_no', 'serial_no', 'posting_date'],
		order_by='posting_date asc',
	)

	for le in ledger_entries:

		# Avoid infinite recursion.
		# if le.voucher_no in visited_nodes:
		#	continue
		visited_nodes[le.voucher_no] = True

		data.append({
			'indent': indent,
			'item_code': le.item_code,
			'item_name': get_name(le.item_code),
			'voucher_type': le.voucher_type,
			'voucher_no': le.voucher_no,
			'batch_no': le.batch_no,
			'serial_no': le.serial_no,
			'production_date': le.posting_date,
		})

		doc = frappe.get_doc(le.voucher_type, le.voucher_no)
		print("Found doc", doc.name)

		# this is either an STE or a PREC.
		if doc.doctype == 'Stock Entry' and doc.stock_entry_type in ['Manufacture', 'Repack']:
			# Find all batched items and start over.
			for item in doc.items:
				#TODO: handle case where same serial no comes in and out - avoid infinite recursion.
				if item.s_warehouse and item.item_code != le.item_code:
					build_tree(data, indent+1, item.batch_no, item.serial_no, visited_nodes)

def get_data(filters):
	# filters.batch_no = '220906_Rinse'

	data = []
	build_tree(data, indent=0, batch_no=filters.batch_no, serial_no=filters.serial_no)
	return data