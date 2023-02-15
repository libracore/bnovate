# Copyright (c) 2023, bNovate, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

from bnovate.bnovate.utils import iot_apis

def execute(filters=None):
	columns = get_columns()
	data = get_data()
	return columns, data

def get_columns():
	return [
		{'fieldname': 'customer', 'fieldtype': 'Link', 'label': _('Customer'), 'options': 'Customer', 'width': 120},
		{'fieldname': 'customer_name', 'fieldtype': 'Data', 'label': _('Customer Name'), 'width': 300}, 
		{'fieldname': 'docname', 'fieldtype': 'Link', 'label': _('Package Name'), 'options': 'Connectivity Package', 'width': 150}, 
		{'fieldname': 'status_indicator', 'fieldtype': 'Data', 'label': _('Status'), 'width': 80}, 
		{'fieldname': 'name', 'fieldtype': 'Data', 'label': _('Device Name'), 'width': 150}, 
		{'fieldname': 'sim_data_usage_mb', 'fieldtype': 'Float', 'label': _('Data Usage [MB]'), 'width': 150}, 
		# {'fieldname': 'item_code', 'fieldtype': 'Link', 'label': _('Item'), 'options': 'Item', 'width': 100},
		# {'fieldname': 'warehouse', 'fieldtype': 'Link', 'label': _('Warehouse'), 'options': 'Warehouse', 'width': 100},
		# {'fieldname': 'purchase_document_no', 'fieldtype': 'Link', 'label': _('Transfer doc'), 'options': 'Stock Entry', 'width': 100}, 
		# {'fieldname': 'purchase_date', 'fieldtype': 'Date', 'label': _('Since date'), 'width': 80},
	]

def get_data(filters=None):
	api_data = { device['serial']: device for device in iot_apis.get_devices_and_data() }
	devices = frappe.get_all("Connectivity Package", 
		fields=["name", "teltonika_serial", "customer", "customer_name"],
		order_by="customer"
	)

	output = []
	prev_customer = None
	for device in devices:
		if not device['teltonika_serial'] in api_data:
			continue
		device['docname'] = device['name']
		device['indent'] = 1
		device.update(api_data[device['teltonika_serial']])
	
		# Group by customer and roll-up data usage:
		if device['customer'] != prev_customer:
			output.append({
				'indent': 0,
				'customer': device['customer'],
				'customer_name': device['customer_name']
			})
		prev_customer = device['customer']

		# Empty redundant fields in child items, add indicators
		device['customer'] = ''
		device['customer_name'] = ''
		if device['status'] == 1:
			device['status_indicator'] = '<a href="https://rms.teltonika-networks.com/devices/{id}" target="_blank"><span class="indicator whitespace-nowrap green"><span>Online <i class="fa fa-external-link"></i></span></span></a>'.format(id=device['id'])
		else:
			device['status_indicator'] = '<a href="https://rms.teltonika-networks.com/devices/{id}" target="_blank"><span class="indicator whitespace-nowrap red"><span>Offline <i class="fa fa-external-link"></i></span></span></a>'.format(id=device['id'])
		output.append(device)

	# Traverse list backwards to calculate totals:
	cumsum = 0
	for device in output[::-1]:
		if device['indent'] == 0: # 'group' row: display and reset
			device['sim_data_usage_mb']	= cumsum
			cumsum = 0
		else: # 'child' row showing individual device usage
			cumsum += device['sim_data_usage_mb']

	return output