# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc, map_child_doc, map_doc

from erpnext.controllers.queries import get_match_cond

BILLING_QUOTATION = "According to Quotation"
BILLING_SERVICE_AGREEMENT = "Under Service Agreement"

class ServiceReport(Document):
	# def autoname(self):
	# 	self.title = "{0} - {1} {2}".format(self.customer_name, self.item_name, self.serial_no)

	def validate(self):
		# Ensure there are no unnecessary links
		if self.billing_basis !=  BILLING_QUOTATION:
			self.quotation = None
		if self.billing_basis != BILLING_SERVICE_AGREEMENT:
			self.subscription_contract = None

	def before_submit(self):
		pass

		# # Check that all items are available in personal stock
		# levels = get_stock_levels(self.set_warehouse)
		# for row in self.items:
		# 	print(row.item_code, row.qty)
		# 	if row.item_code in levels and levels[row.item_code] >= row.qty:
		# 		continue
		# 	raise Exception("Insufficiant stock for item {item_code}.".format(item_code=row.item_code))


@frappe.whitelist()
def make_from_template(source_name, target_doc=None):
	return _make_from_template(source_name, target_doc)

def _make_from_template(source_name, target_doc, ignore_permissions=False):
	def postprocess(source, target):

		# Default mapping puts all child items of same doctype into the first matching table.
		# Instead, reset and separate according to parent field:
		target.items = []
		target.labour_travel = []

		for source_d in source.get('items', []):
			target_d = frappe.new_doc(source_d.doctype, target, 'items')
			map_doc(source_d, target_d, {}, source)
			target_d.idx = None
			target.append('items', target_d)

		for source_d in source.get('labour_travel', []):
			target_d = frappe.new_doc(source_d.doctype, target, 'labour_travel')
			map_doc(source_d, target_d, {}, source)
			target_d.idx = None
			target.append('labour_travel', target_d)


	doclist = get_mapped_doc("Service Report Template", source_name, {
			"Service Report Template": {
				"doctype": "Service Report",
				# "validation": {
				# 	"docstatus": ["=", 1]
				# }
				"field_no_map": [
					'title', # Ignore template title
				]
			},
			# "Service Report Item": {
			# 	"doctype": "Service Report Item",
			# 	"field_map": {
			# 		"parentfield": "parentfield",
			# 	},
			# },
		}, target_doc, postprocess, ignore_permissions=ignore_permissions)

	return doclist

@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
	return _make_sales_order(source_name, target_doc)

def _make_sales_order(source_name, target_doc, ignore_permissions=False):

	def set_missing_values(source, target):
		# if customer:
		# 	target.customer = customer.name
		# 	target.customer_name = customer.customer_name
		target.delivery_date = source.intervention_date
		target.ignore_pricing_rule = 1
		# target.flags.ignore_permissions = ignore_permissions

		for item in target.items:
			item.delivery_date = source.intervention_date

		if source.billing_basis == BILLING_SERVICE_AGREEMENT:
			for item in target.items:
				item.discount_percentage = 100

	# def update_item(obj, target, source_parent):
	# 	target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)

	doclist = get_mapped_doc("Service Report", source_name, {
			"Service Report": {
				"doctype": "Sales Order",
				"field_map": {
					"intervention_date": "transaction_date",

				},
				"validation": {
					"docstatus": ["=", 1]
				}
			},
			"Service Report Item": {
				"doctype": "Sales Order Item",
				# "field_map": {
				# 	"parent": "prevdoc_docname"
				# },
				# "condition": is_subscription_item,
				# "postprocess": update_item
			},
		}, target_doc, set_missing_values, ignore_permissions=ignore_permissions)

	return doclist

def get_stock_levels(warehouse):
	data = frappe.db.sql("""
		SELECT
			item_code,
			actual_qty
		FROM `tabBin`
		WHERE warehouse = "{warehouse}"
	""".format(warehouse=warehouse), as_dict=True)

	return { row.item_code: row.actual_qty for row in data}

@frappe.whitelist()
def item_query(doctype, txt, searchfield, start, page_len, filters):
	warehouse = filters.get("warehouse")
	return frappe.db.sql("""
		SELECT
			it.item_code,
			CONCAT(ROUND(bin.actual_qty, 0), " ", bin.stock_uom, " in stock"),
			if(length(it.item_name) > 40, concat(substr(it.item_name, 1, 40), "..."), it.item_name) as item_name,
			if(length(it.description) > 40, concat(substr(it.description, 1, 40), "..."), it.description) as decription
		FROM `tabBin` bin
		JOIN `tabItem` it on it.item_code = bin.item_code
		WHERE bin.warehouse = "{warehouse}"
			AND bin.actual_qty > 0
			AND (it.item_code LIKE "%{txt}%" or it.item_name LIKE "%{txt}%")
			{match_conditions}
	""".format(txt=txt, warehouse=warehouse, match_conditions=get_match_cond(doctype)))