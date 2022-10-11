# Copyright (c) 2021, bNovate, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{'fieldname': 'expected_delivery_date', 'fieldtype': 'Date', 'label': _('Expected date'), 'width': 80},
		# {'fieldname': 'item_name', 'fieldtype': 'Data', 'label': _('Item Name'), 'width': 300},
		{'fieldname': 'remaining_qty', 'fieldtype': 'Int', 'label': _('Qty Remaining'), 'width': 100},
		{'fieldname': 'item', 'fieldtype': 'Link', 'label':_('Item'), 'options': 'Item', 'width': 400},
		{'fieldname': 'comment', 'fieldtype': 'Text', 'label': _('Comment'), 'width': 200},
		{'fieldname': 'work_order', 'fieldtype': 'Link', 'label': _('Work Order'), 'options': 'Work order', 'width': 80},
		{'fieldname': 'item_group', 'fieldtype': 'Data', 'label': _('Item Group'), 'width': 100},
	]

def get_data(filters):
	print(filters)
	extra_filters = ""
	if filters.bnovate_contact:
		extra_filters += "AND po.bnovate_person = '{}'\n".format(filters.bnovate_contact)
	if filters.only_stock_items:
		extra_filters += "AND it.is_stock_item = {}\n".format(filters.only_stock_items)

	sql_query = """
SELECT
  wo.name as work_order,
  wo.expected_delivery_date,
  wo.production_item as item,
  wo.item_name as item_name,
  (wo.qty - wo.produced_qty) as remaining_qty,
  wo.comment,
  it.item_group
FROM `tabWork Order` as wo
JOIN `tabItem` as it on wo.production_item = it.name
WHERE 
	wo.status NOT IN ("Completed", "Cancelled", "Stopped")
	AND item_group IN ("New Cartridges", "Cartridge Refills", "Chemicals", "Chemical Kits")
ORDER BY expected_delivery_date
	""".format(extra_filters=extra_filters)

	data = frappe.db.sql(sql_query, as_dict=True)


	for row in data:
		row['comment'] = """<p title="{value}">{value}</p>""".format(value=row['comment'])

	return data