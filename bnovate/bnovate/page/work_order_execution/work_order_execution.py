# -*- coding: utf-8 -*-
# Copyright (c) 2017-2022, bnovate, libracore and contributors
#

# These methods require some custom fields on work orders:
#
# - time_log: table of "Work Order Time Log" child items. These have a datetime start_time and end_time field, and a float duration field.
#           start_time is mandatory, all can be changed after submit.
# - total_time: float, total duration in minutes.
#

from __future__ import unicode_literals
import frappe
from frappe import throw, _
import hashlib
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
    for row in wo.time_log:
        if row.end_time is None:
            row.end_time = datetime.now()
            row.duration = (row.end_time - row.start_time).total_seconds() / 60

            wo.save()
            frappe.db.commit()
            return

    # If we reached this point, no logs were open
    frappe.msgprint("Time logging hasn't been started yet, therefore it can't be stopped.", raise_exception=True)


def calculate_total_time(doc, method=None):
    wo = doc
    for row in wo.time_log:
        if row.end_time is None:
            continue
        row.duration = (row.end_time - row.start_time).total_seconds() / 60

    wo.total_time = sum([row.duration for row in wo.time_log if row.duration is not None])
    print("Calculating total time for WO:", wo.total_time)
    # wo_doc.save()
    # frappe.db.commit()

#TODO: method that calculates total time and time per part. Use frappe hooks to call when WO is saved.
# See https://youtu.be/GGdWRe-aoxA?t=383
