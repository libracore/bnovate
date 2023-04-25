# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class RefillRequest(Document):

    def validate(self):
        self.set_status()

    def on_cancel(self):
        self.set_status()

    def set_status(self):

        if self.docstatus == 2:
            self.status = "Cancelled"
        elif self.docstatus == 1:
            self.status = "Submitted"
            if self.has_sales_order():
                self.status = "Confirmed"
        else:
            self.status = "Draft"

        self.db_set("status", self.status)

    def has_sales_order(self):
        return frappe.db.get_value("Sales Order Item", {"refill_request": self.name, "docstatus": 1})


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

        if tcc_sns:
            target.append("items", {
                "item_code": '200019',
                "description": "<br>".join(tcc_sns),
                "qty": len(tcc_sns),
                "refill_request": source.name,
            })
        if icc_sns:
            target.append("items", {
                "item_code": '200054',
                "description": "<br>".join(icc_sns),
                "qty": len(icc_sns),
                "refill_request": source.name,
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

def update_status_from_sales_order(sales_order, method=None):
    # Called by hooks.py when an SO changes.
    if not method in ('on_submit', 'on_cancel'):
        return

    for rr in list(set([it.refill_request for it in sales_order.get("items")])):
        if rr:
            doc = frappe.get_doc("Refill Request", rr)
            doc.set_status()
