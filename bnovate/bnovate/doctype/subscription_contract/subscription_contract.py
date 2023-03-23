# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, nowdate, getdate, add_days, date_diff
from erpnext.selling.doctype.quotation.quotation import _make_customer
from erpnext.controllers.sales_and_purchase_return import make_return_doc

class SubscriptionContract(Document):
	pass

@frappe.whitelist()
def make_from_quotation(source_name, target_doc=None):
	quotation = frappe.db.get_value("Quotation", source_name, ["transaction_date", "valid_till"], as_dict = 1)
	if quotation.valid_till and (quotation.valid_till < quotation.transaction_date or quotation.valid_till < getdate(nowdate())):
		frappe.throw(_("Validity period of this quotation has ended."))
	return _make_from_quotation(source_name, target_doc)

def _make_from_quotation(source_name, target_doc=None, ignore_permissions=False):
	customer = _make_customer(source_name, ignore_permissions)

	def set_missing_values(source, target):
		if customer:
			target.customer = customer.name
			target.customer_name = customer.customer_name
		target.ignore_pricing_rule = 1
		target.flags.ignore_permissions = ignore_permissions

	def update_item(obj, target, source_parent):
		target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)

	doclist = get_mapped_doc("Quotation", source_name, {
			"Quotation": {
				"doctype": "Subscription Contract",
				"validation": {
					"docstatus": ["=", 1]
				}
			},
			"Quotation Item": {
				"doctype": "Subscription Contract Item",
				"field_map": {
					"parent": "prevdoc_docname"
				},
				"condition": is_subscription_item,
				"postprocess": update_item
			},
			"Sales Taxes and Charges": {
				"doctype": "Sales Taxes and Charges",
				"add_if_empty": True
			},
		}, target_doc, set_missing_values, ignore_permissions=ignore_permissions)

	return doclist

def is_subscription_item(quotation_item):
	""" Return true if item line from QTN is a subscription-able item """
	return bool(frappe.db.get_value("Item", quotation_item.item_code, "enable_deferred_revenue"))

@frappe.whitelist()
def make_from_self(source_name, target_doc=None):
	""" Make a copy of the subscription, but starting at the end date of previous one.

	Can be used to renew or modify (upgrade) a subscription.
	"""
	closing_doc = frappe.db.get_value("Subscription Contract", source_name, ["end_date"], as_dict=1)

	end_date = closing_doc.end_date
	if not end_date:
		end_date = nowdate()
	
	def postprocess(source, target):
		target.start_date = add_days(end_date, 1) 
		target.end_date = None
		target.planned_end_date = None

	return get_mapped_doc("Subscription Contract", source_name, {
		"Subscription Contract": {
			"doctype": "Subscription Contract",
		}
	}, postprocess=postprocess)

@frappe.whitelist()
def close(docname, end_date=None):
	""" Set end date of a subscription """
	if end_date is None:
		end_date = nowdate()

	doc = frappe.get_doc("Subscription Contract", docname)
	doc.db_set("end_date", end_date)

	# Find associated sales invoice items and matching credit notes, if any
	items = [it.name for it in doc.items]
	query = """
	WITH sinv_items as (
		SELECT
			sii.parent as sinv_name,
			sii.name,
			sii.service_start_date,
			sii.service_end_date,
			sii.service_stop_date,
			sii.idx,
			sii.net_amount,
			sii.sc_detail,
			si.currency
		FROM `tabSales Invoice Item` sii
		JOIN `tabSales Invoice` si ON sii.parent = si.name
		WHERE sii.sc_detail IN {items} 
			AND sii.docstatus <= 1
			AND si.is_return = 0
	), ret_items as (
		SELECT
			sii.parent as credit_note,
			sii.net_amount as refunded_amount,
			sii.sc_detail,
			sii.service_start_date
		FROM `tabSales Invoice Item` sii
		JOIN `tabSales Invoice` si ON sii.parent = si.name
		WHERE sii.sc_detail IN {items}
			AND sii.docstatus <= 1
			AND si.is_return = 1
	)
	SELECT 
		sinv_items.*,
		credit_note,
		refunded_amount
	FROM sinv_items
	LEFT JOIN ret_items ON sinv_items.sc_detail = ret_items.sc_detail AND sinv_items.service_start_date = ret_items.service_start_date
	""".format(items='("' + '", "'.join(items) + '")')
	sinv_items = frappe.db.sql(query, {'items': items}, as_dict=True)

	print(sinv_items)

	# For any item within current or future billing period (relative to end_date), stop service early
	# and calculate refund amount
	to_modify = {}
	refunds = {}
	matching_items = []
	for si in sinv_items:
		if getdate(end_date) < si.service_end_date and si.refunded_amount is None:

			matching_items.append(si)

			if si.sinv_name not in to_modify:
				to_modify[si.sinv_name] = [si]
			else:
				to_modify[si.sinv_name].append(si)

			stop_date = max(getdate(end_date), si.service_start_date)
			frappe.db.set_value("Sales Invoice Item", si.name, "service_stop_date", stop_date)

			# Calculate refund amount
			period_days = (si.service_end_date - si.service_start_date).days
			remaining_days = (si.service_end_date - stop_date).days

			si.refund = si.net_amount * remaining_days / period_days

			if si.sc_detail not in refunds:
				refunds[si.sc_detail] = {}

			refunds[si.sc_detail][si.service_start_date] = si.refund

	return matching_items


	# Create Credit Note for each invoice
	for sinv_name, items in to_modify.items():
		# Inspired by make_mapped_doc: flags are read by get_mapped_doc, which is called
		# by make_return_doc()
		frappe.flags.selected_children = {'items': [ it.name for it in items]}
		sinv_ret = make_return_doc("Sales Invoice", sinv_name)
		sinv_ret.naming_series = "SINV-RET-"

		# Set refund amount
		for item in sinv_ret.items:
			item.rate = refunds[item.sc_detail][item.service_start_date]
			item.enable_deferred_revenue = False

		sinv_ret.insert()
		print(sinv_ret)

	frappe.msgprint("Modified these invoices: {}".format(to_modify.keys()))


