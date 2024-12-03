# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import getdate, add_days

from erpnext import get_default_company
from erpnext.stock.get_item_details import get_item_details

from bnovate.bnovate.utils import get_contact_display

class RefillRequest(Document):

    def validate(self):
        self.set_status()

    def on_cancel(self):
        self.set_status()

    @property
    def contact_display(self):
        return get_contact_display(self.contact_person)

    def set_status(self):

        if self.docstatus == 2:
            self.status = "Cancelled"
        elif self.docstatus == 1:
            self.status = "Requested"
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
            "Requested": "orange",
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

    def set_tracking_url(self):
        self.tracking_url = None
        if self.carrier == "DHL":
            self.tracking_url = "https://www.dhl.com/ch-en/home/tracking/tracking-express.html?submit=1&tracking-id={0}".format(self.tracking_no)
    

def get_context(context):
    context.title = "My title"
    return context


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):

    def set_missing_values(source, target):

        customer = frappe.get_doc("Customer", source.customer)

        # Map request items to sales order items.
        tcc_sns = list(set(row.serial_no for row in source.items if row.type == "TCC"))
        icc_sns = list(set(row.serial_no for row in source.items if row.type == "ICC"))
        icp_sns = list(set(row.serial_no for row in source.items if row.type == "ICC+"))

        item_code_tcc = '200019'
        item_code_icc = '200054'
        item_code_icp = '200141.02'

        target_copy = target.as_dict()
            
        def get_item_deets(item_code):
            return get_item_details(args=target_copy.update({
                'item_code': item_code,
                'transaction_date': getdate(),
            }))

        if tcc_sns:
            deets = get_item_deets(item_code_tcc)
            fields = {
                "item_code": item_code_tcc,
                "serial_nos": "\n".join(tcc_sns),
                "qty": len(tcc_sns),
                "refill_request": source.name,
                "rate": deets.blanket_order_rate,
                "weight_per_unit": deets.weight_per_unit,
                "total_weight": len(tcc_sns) * deets.weight_per_unit,
            }
            if deets.blanket_order:
                fields["blanket_order"] = deets.blanket_order
            elif customer.default_discount:
                fields["discount_percentage"] = customer.default_discount
            target.append("items", fields)

        if icc_sns:
            deets = get_item_deets(item_code_icc)
            fields = {
                "item_code": item_code_icc,
                "serial_nos": "\n".join(icc_sns),
                "qty": len(icc_sns),
                "refill_request": source.name,
                "rate": deets.blanket_order_rate,
                "weight_per_unit": deets.weight_per_unit,
                "total_weight": len(icc_sns) * deets.weight_per_unit,
            }
            if deets.blanket_order:
                fields["blanket_order"] = deets.blanket_order
            elif customer.default_discount:
                fields["discount_percentage"] = customer.default_discount
            target.append("items", fields)

        if icp_sns:
            deets = get_item_deets(item_code_icp)
            fields = {
                "item_code": item_code_icp,
                "serial_nos": "\n".join(icp_sns),
                "qty": len(icp_sns),
                "refill_request": source.name,
                "rate": deets.blanket_order_rate,
                "weight_per_unit": deets.weight_per_unit,
                "total_weight": len(icp_sns) * deets.weight_per_unit,
            }
            if deets.blanket_order:
                fields["blanket_order"] = deets.blanket_order
            elif customer.default_discount:
                fields["discount_percentage"] = customer.default_discount
            target.append("items", fields)

        if source.return_label_needed:
            target.order_level_requests = "Organize return from customer, {} parcels.\n".format(source.parcel_count or 1) + (source.remarks or "")

        target.contact_display = source.contact_display

        # force empty some fields so they get set from customer defaults
        target.currency = None
        target.selling_price_list = None
        target.price_list_currency = None
        target.default_discount = customer.default_discount
        target.total_net_weight = sum([item.total_weight for item in target.items])
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
        if so_name is not None:
            so = frappe.get_doc("Sales Order", so_name)
            update_status_from_sales_order(so, method='dn_update')