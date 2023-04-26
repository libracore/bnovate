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
            if self.has_shipped():
                self.status = "Shipped"
            elif self.has_sales_order():
                self.status = "Confirmed"
        else:
            self.status = "Draft"

        self.db_set("status", self.status)
        self.set_tracking(self.has_shipped())

    def set_indicator(self):
        # Like status but for the portal
        status_color = {
            "Draft": "red",
            "Submitted": "orange",
            "Confirmed": "blue",
            "Shipped": "green",
            "Cancelled": "darkgrey",
        }
        self.indicator_title = self.status
        self.indicator_color = status_color[self.status]

    def has_sales_order(self):
        return frappe.db.get_value("Sales Order Item", {"refill_request": self.name, "docstatus": 1})

    def has_shipped(self):
        so_detail = frappe.db.get_value("Sales Order Item", {"refill_request": self.name, "docstatus": 1}) 
        dn = frappe.db.get_value("Delivery Note Item", {"so_detail": so_detail, "docstatus": 1}, 'parent') 
        return dn

    def set_tracking(self, dn=None):
        if dn is None:
            self.db_set("tracking_no", None)
            self.db_set("carrier", None)
            return
        dn_doc = frappe.get_doc("Delivery Note", dn)
        self.db_set("tracking_no", dn_doc.tracking_no)
        self.db_set("carrier", dn_doc.carrier)


def get_context(context):
    context.title = "My title"
    return context


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):

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
                "transaction_date": "po_date",
                "remarks": "order_level_requests",
            },
        },
    }, target_doc, set_missing_values, ignore_permissions=False)
    return doclist

def update_status_from_sales_order(sales_order, method=None):
    # Called by hooks.py when an SO changes or by DN below...
    if not method in ('on_submit', 'on_cancel', 'dn_update'):
        return

    for rr in list(set([it.refill_request for it in sales_order.get("items")])):
        if rr:
            doc = frappe.get_doc("Refill Request", rr)
            doc.set_status()

            if method == 'on_submit':
                doc.db_set("expected_ship_date", sales_order.delivery_date)
            elif method == 'on_cancel':
                doc.db_set("expected_ship_date", None)

def update_status_from_delivery_note(delivery_note, method=None):
    # Called by hooks.py when a DN changes
    if not method in ('on_submit', 'on_cancel', 'on_update_after_submit'):
        return

    for so_name in list(set([it.against_sales_order for it in delivery_note.get("items")])):
        so = frappe.get_doc("Sales Order", so_name)
        update_status_from_sales_order(so, method='dn_update')