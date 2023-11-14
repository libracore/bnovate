# Override standard message page (that shows errors and other messages),
# to redirect users after login using javascript.

import frappe
from frappe.www import message
from frappe import _

def get_context(context):

    # return_to_path is set by auth() when auth fails.
    if getattr(frappe.local, 'return_to_path', None) is not None:
        context.return_to_path = frappe.local.return_to_path

    context.update(message.get_context(context))
    return context