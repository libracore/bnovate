# -*- coding: utf-8 -*-
# Copyright (c) 2017-2022, bnovate, libracore and contributors
#

# These methods require some custom fields on work orders:
#
# - time_log: table of "Work Order Time Log" child items. These have a datetime start_time and end_time field, and a float duration field.
#           start_time is mandatory, duration is read-only. All can be changed after submit.
# - total_time: float, total duration in minutes. Read only, allowed on submit.
# - time_per_unit
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
    frappe.db.commit()
    return

@frappe.whitelist()
def stop_log(work_order_id):
    """ Update end time on current time log, calculate duration"""
    wo = frappe.get_doc("Work Order", work_order_id)
    for row in wo.time_log[::-1]: # Finish most recent row if there happens to be several
        if row.end_time is None:
            row.end_time = datetime.now()

            wo.save()
            frappe.db.commit()
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
    # If we wanted time per unit, we would need hooks on Stock Entry, after submit and after cancel.
    wo.db_set("time_per_unit", wo.time_per_unit)

def update_work_order_unit_time(stock_entry, method=None):
    """ Re-calculate per-unit time on work orders after a stock entry has changed produced qty.
    
    Called by hooks.py
    """
    if stock_entry.purpose != "Manufacture":
        return

    wo = frappe.get_doc("Work Order", stock_entry.work_order)
    calculate_total_time(wo)

#TODO: method that calculates total time and time per part. Use frappe hooks to call when WO is saved.
# See https://youtu.be/GGdWRe-aoxA?t=383
