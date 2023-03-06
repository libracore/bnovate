# Copyright (c) 2023, bNovate, libracore, and contributors
# For license information, please see license.txt
#
# WORK ORDER PLANNING
#####################
#
# Show which open work orders are executable based on inventory levels.
#
###################################################################

from __future__ import unicode_literals
import frappe
from frappe import _
from collections import OrderedDict

from urllib.parse import quote

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{'fieldname': 'sufficient_stock', 'fieldtype': 'Data', 'label': _('Go?'), 'width': 50},
		{'fieldname': 'work_order', 'fieldtype': 'Link', 'label': _('Work Order'), 'options': 'Work Order', 'width': 100},
		{'fieldname': 'workstation', 'fieldtype': 'Data', 'label': _('Workstation'), 'width': 100},
		{'fieldname': 'status', 'fieldtype': 'Data', 'label': _('Status'), 'width': 100},
		{'fieldname': 'planned_start_date', 'fieldtype': 'Date', 'label': _('Start date'), 'width': 80},
		# {'fieldname': 'item_name', 'fieldtype': 'Data', 'label': _('Item Name'), 'width': 300},
		{'fieldname': 'required_qty', 'fieldtype': 'Int', 'label': _('Qty Required'), 'width': 100},
		{'fieldname': 'item', 'fieldtype': 'Link', 'label':_('Item'), 'options': 'Item', 'width': 200},
		{'fieldname': 'comment', 'fieldtype': 'Text', 'label': _('Comment'), 'width': 200},
		{'fieldname': 'item_group', 'fieldtype': 'Data', 'label': _('Item Group'), 'width': 100},
		{'fieldname': 'available_stock', 'fieldtype': 'Int', 'label': _('Stock'), 'width': 70},
		{'fieldname': 'warehouse', 'fieldtype': 'Data', 'label': _('Warehouse'), 'width': 100},
	]

def get_data(filters):

	# Build a list of all open work orders with required item qties,
	# and a dict of item stock levels.
	# In order of planned start date, decrement stock levels and check if
	# sufficient to start the work order.

	sql_query = """
	SELECT 
		wo.name AS work_order,
		wo.production_item,
		DATE(wo.planned_start_date) AS planned_start_date,
		wo.planned_end_date,
		wo.qty as planned_qty,
		wo.produced_qty,
		(wo.qty - wo.produced_qty) AS required_qty,
		wo.status,
		wo.comment,
		wo.workstation,
		wo.fg_warehouse,
		it.item_group,
		it.item_name,
		
		woi.item_code,
		-- woi.item_group AS reqd_item_group:
		woi.source_warehouse,
		woi.required_qty AS item_qty,
		woi.consumed_qty AS item_consumed_qty,
		(woi.required_qty - woi.consumed_qty) AS item_still_needed_qty,
		woi.item_name as reqd_item_name
	FROM `tabWork Order Item` woi
	JOIN `tabWork Order` wo on woi.parent = wo.name
	JOIN `tabItem` it on it.item_code = wo.production_item
	WHERE wo.status NOT IN ("Completed", "Cancelled", "Stopped")
	ORDER BY wo.planned_start_date, wo.name
	""".format()
	data = frappe.db.sql(sql_query, as_dict=True)

	# Group by work order, create list of required items on each work_order, same structure
	# as if we were able to get child items with frappe.get_all:
	#
	# Out of laziness, there are unnecessary keys in each dict (item params in WO, WO params in item)
	items = set()
	wos = OrderedDict()
	for r in data:
		items.add(r['item_code'])
		name = r['work_order']
		if name not in wos:
			wo = dict(r)  # shallow copy to avoid circular ref
			wo['items'] = []
			wos[name] = wo
		wos[name]['items'].append(dict(r))  

	#

	# Stock levels
	sql_query = """
	SELECT 
		item_code,
		warehouse,
		actual_qty
	FROM tabBin
	WHERE item_code IN {items}
	""".format(items=tuple(items)) # python tuple prints nicely for SQL IN filter.
	stock_raw = frappe.db.sql(sql_query, as_dict=True)

	stock = {} # stock[warehouse][item_code] = actual_qty
	for r in stock_raw:
		warehouse, item = r['warehouse'], r['item_code']
		if warehouse not in stock:
			stock[warehouse] = {}
		stock[warehouse][item] = r['actual_qty']


	# Check stock requirements and levels for each WO:
	data = []
	idx = 0
	for _, wo in wos.items():
		sufficient_stock = True
		data.append(wo)
		for item in wo['items']:
			required = item['item_still_needed_qty']
			available = stock[item['source_warehouse']][item['item_code']]
			sufficient_item_stock = True if available >= required else False

			item['sufficient_stock'] = sufficient_item_stock
			item['available_stock'] = available

			stock[item['source_warehouse']][item['item_code']] -= required
			sufficient_stock = sufficient_stock and sufficient_item_stock

			item['indent'] = 1
			item['item'] = item['item_code']
			item['item_name'] = item['reqd_item_name']
			item['required_qty'] = required
			item['item_group'] = None  # Avoid confusion with production item's group
			item['warehouse'] = item['source_warehouse']
			data.append(item)
		wo['sufficient_stock'] = sufficient_stock
		wo['indent'] = 0
		wo['item'] = wo['production_item']
		wo['idx'] = idx
		wo['warehouse'] = wo['fg_warehouse']
		idx += 1

	# import pprint
	# pp = pprint.PrettyPrinter(indent=4)
	# print("\n\n\n------", pp.pprint(stock))
	# print("\n\n\n------", pp.pprint(wos))
	# Only filter on workstation AFTER we've calculated stock levels

	if filters.workstation:
		data = [d for d in data if d['workstation'] == filters.workstation]

	return data
