# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, nowdate, getdate, add_days, date_diff
from erpnext.selling.doctype.quotation.quotation import _make_customer

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

	# Find associated sales invoice iems (#TODO: exclude credit notes)
	items = [it.name for it in doc.items]
	sinv_items = frappe.db.get_all("Sales Invoice Item", 
		filters={ 'sc_detail': ['IN', tuple(items)] },
		fields=['name', 'service_start_date', 'service_end_date', 'service_stop_date', 'idx', 'parent', 'net_amount']
	)

	# For any item within current or future billing period (relative to end_date), stop service early
	modified = []
	for si in sinv_items:
		if getdate(end_date) < si.service_end_date:
			modified.append(si.parent)
			stop_date = max(getdate(end_date), si.service_start_date)
			frappe.db.set_value("Sales Invoice Item", si.name, "service_stop_date", stop_date)

			# Calculate refund amount
			period_days = (si.service_end_date - si.service_start_date).days
			remaining_days = (si.service_end_date - stop_date).days

			si.refund = si.net_amount * remaining_days / period_days

	# TODO: relay list of modified SINV items back to user
	print("\n\n\n--------------------------------------------")
	print(modified, sinv_items)
	frappe.msgprint("Modified these invoices: {}".format(set(modified)))
	frappe.msgprint(sinv_items)


