# -*- coding: utf-8 -*-
# Copyright (c) 2017-2022, bnovate, libracore and contributors
#

# These methods require some custom fields on work orders:
#
# - time_log: table of "Work Order Time Log" child items. These have a datetime start_time and end_time field, and a float duration field.
#           start_time is mandatory, duration is read-only. All can be changed after submit.
# - total_time: float, total duration in minutes. Read only, allowed on submit.
# - time_per_unit: same config as total_time.
#

from __future__ import unicode_literals
import frappe
from frappe import throw, _
from frappe.utils import get_datetime
from datetime import datetime, timedelta

@frappe.whitelist()
def start_log(work_order_id):
    """ Add a row to time tracking with current time as start time. """
    wo = frappe.get_doc("Work Order", work_order_id)
    # Check if an open time log exists. If so, raise error. Should pause first.
    if None in [ row.end_time for row in wo.time_log ]:
        return frappe.msgprint("Time logging has already started on this work order.", raise_exception=True)
    row = wo.append('time_log', {
        'start_time': datetime.now(),
    })
    wo.save()
    return

@frappe.whitelist()
def stop_log(work_order_id):
    """ Update end time on current time log, calculate duration"""
    wo = frappe.get_doc("Work Order", work_order_id)
    for row in wo.time_log[::-1]: # Finish most recent row if there happens to be several
        if row.end_time is None:
            row.end_time = datetime.now()

            wo.save()
            return

    # If we reached this point, no logs were open
    frappe.msgprint("Time logging hasn't been started yet, therefore it can't be stopped.", raise_exception=True)


def calculate_total_time(doc, method=None):
    """ Calculate total time per WO and per produced part. Called by hooks.py  """
    wo = doc
    for row in wo.time_log:
        if row.end_time is None:
            row.duration = 0
        else:
            row.duration = (get_datetime(row.end_time) - get_datetime(row.start_time)).total_seconds() / 60
        row.db_set("duration", row.duration)

    wo.total_time = sum([row.duration for row in wo.time_log if row.duration is not None])
    wo.time_per_unit = 0 if wo.produced_qty == 0 else wo.total_time / wo.produced_qty
    wo.db_set("total_time", wo.total_time)
    wo.db_set("time_per_unit", wo.time_per_unit)

    update_work_order_status(wo)

def update_work_order_unit_time(stock_entry, method=None):
    """ Re-calculate per-unit time on work orders after a stock entry has changed produced qty.
    
    Called by hooks.py
    """
    if stock_entry.purpose != "Manufacture":
        return

    wo = frappe.get_doc("Work Order", stock_entry.work_order)
    calculate_total_time(wo)

def update_work_order_status_from_ste(stock_entry, method=None):
    """ Set work order status to In Process if draft STEs exist.
     
    Called by hooks.py
    """

    if stock_entry.purpose != "Manufacture":
        return

    wo = frappe.get_doc("Work Order", stock_entry.work_order)
    new_ste = None
    if method == "before_save":
        new_ste = stock_entry
    return update_work_order_status(wo, new_ste)

def update_work_order_status(wo, new_ste=None):
    status = wo.get_status()
    if status == "Not Started":
        # Override default behaviour: if draft STE exist or time logging has started, the WO is In Process. If not, keep Not Started
        draft_stock_entries = frappe.db.get_all("Stock Entry", filters={'work_order': ['=', wo.name], 'docstatus': ['=', 0]})
        if new_ste and new_ste.docstatus == 0:
            # In this specific situation, the draft isn't yet in the DB.
            draft_stock_entries.append(new_ste)
        if draft_stock_entries or wo.time_log:
            wo.db_set("status", "In Process")
        else: 
            wo.db_set("status", status)


#######################################
# Autonumbering
#######################################

@frappe.whitelist()
def make_auto_serial_no(item_code):
    from erpnext.stock.doctype.serial_no import serial_no as sn
    item_master = frappe.get_doc("Item", item_code)
    if not (item_master.has_serial_no and item_master.serial_no_series):
        frappe.throw("Item {} needs to be serialized and needs serial no series".format(item_code))

    serial_no = sn.get_auto_serial_nos(item_master.serial_no_series, 1)
    return serial_no
