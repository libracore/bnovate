# Copyright (c) 2025, bNovate, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	if not filters: filters = {}

	columns = get_columns(filters)

	data = get_bom_stock(filters)

	return columns, data

def get_columns(filters):
	"""return columns"""

	columns = [
		{
			"label": _("Item"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 300
		},
		{
			"label": _("Qty per BOM Line"),
			"fieldname": "bom_qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Required Qty"),
			"fieldname": "required_qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("In Stock Qty"),
			"fieldname": "stock_qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Enough to build"),
			"fieldname": "enough_parts_to_build",
			"fieldtype": "Float",
			"width": 200
		},
	]

	return columns

def get_bom_stock(filters):
	conditions = ""
	bom = filters.get("bom")

	table = "`tabBOM Item`"
	qty_field = "qty"

	qty_to_produce = filters.get("qty_to_produce", 1)
	if  int(qty_to_produce) <= 0:
		frappe.throw(_("Quantity to Produce can not be less than Zero"))

	if filters.get("show_exploded_view"):
		table = "`tabBOM Explosion Item`"
		qty_field = "stock_qty"

	if filters.get("warehouse"):
		warehouse_details = frappe.db.get_value("Warehouse", filters.get("warehouse"), ["lft", "rgt"], as_dict=1)
		if warehouse_details:
			conditions += " and exists (select name from `tabWarehouse` wh \
				where wh.lft >= %s and wh.rgt <= %s and ledger.warehouse = wh.name)" % (warehouse_details.lft,
				warehouse_details.rgt)
		else:
			conditions += " and ledger.warehouse = %s" % frappe.db.escape(filters.get("warehouse"))

	else:
		conditions += ""

	return frappe.db.sql("""
			SELECT
				bom_item.item_code,
				item.item_name,
				bom_item.description,
				bom_item.{qty_field} as bom_qty,
				bom_item.{qty_field} * {qty_to_produce} as required_qty,
				sum(ledger.actual_qty) as stock_qty,
				sum(FLOOR(ledger.actual_qty / bom_item.{qty_field})) as enough_parts_to_build
			FROM
				{table} AS bom_item
				LEFT JOIN `tabItem` AS item ON bom_item.item_code = item.item_code
				LEFT JOIN `tabBin` AS ledger
				ON bom_item.item_code = ledger.item_code
				{conditions}
			WHERE
				bom_item.parent = '{bom}' and bom_item.parenttype='BOM'

			GROUP BY bom_item.item_code""".format(
				qty_field=qty_field,
				table=table,
				conditions=conditions,
				bom=bom,
				qty_to_produce=qty_to_produce or 1)
			, as_dict=True)
