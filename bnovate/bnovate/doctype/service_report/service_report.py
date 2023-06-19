# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class ServiceReport(Document):
	pass

@frappe.whitelist()
def make_from_template(source_name, target_doc=None):
	return _make_from_template(source_name, target_doc)

def _make_from_template(source_name, target_doc, ignore_permissions=False):
	def set_missing_values(source, target):
		pass

	doclist = get_mapped_doc("Service Report Template", source_name, {
			"Service Report Template": {
				"doctype": "Service Report",
				# "field_map": {
				# 	"intervention_date": "transaction_date",
				# },
				# "validation": {
				# 	"docstatus": ["=", 1]
				# }
			},
			"Service Report Item": {
				"doctype": "Service Report Item",
			},
		}, target_doc, set_missing_values, ignore_permissions=ignore_permissions)

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