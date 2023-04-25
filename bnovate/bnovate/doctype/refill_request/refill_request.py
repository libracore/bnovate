# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class RefillRequest(Document):
	pass


def get_context(context):
	context.title = "My title"
	return context


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):

	# TODO: how to set Refill request as confirmed?

	def set_missing_values(source, target):
		# Map request items to sales order items.
		tcc_sns = list(set(row.serial_no for row in source.items if row.type == "TCC"))
		icc_sns = list(set(row.serial_no for row in source.items if row.type == "ICC"))

		target.append("items", {
			"item_code": '200019',
			"description": "<br>".join(tcc_sns),
			"qty": len(tcc_sns)
		})
		target.append("items", {
			"item_code": '200054',
			"description": "<br>".join(icc_sns),
			"qty": len(icc_sns)
		})

		target.run_method("set_missing_values")

	doclist = get_mapped_doc("Refill Request", source_name, {
		"Refill Request": {
			"doctype": "Sales Order",
			"validation": {
				"docstatus": ["=", 1]
			},
			"field_map": {
				"billing_address": "customer_address",
				"shipping_address": "shipping_address_name",
				"name": "po_no",
				"creation": "po_date",
				"remarks": "order_level_requests",
			},
		},
	}, target_doc, set_missing_values, ignore_permissions=False)
	return doclist