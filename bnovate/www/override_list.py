# Copyright (c) 2013-2025, bnovate, libracore and contributors
# For license information, please see license.txt

from frappe import _

def get_context(context):
    """ Called by hooks.py as a 'middleware' after frappe.wwwl.list.get_context """
    context.title = _(context.title)
    return context

