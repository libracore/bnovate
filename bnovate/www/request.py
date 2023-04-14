# Show data from a single request

import frappe

from frappe import _

from .helpers import get_session_primary_customer, auth

no_cache = 1

auth()

print("--------------------\n\n\n\nRequest called")

def get_context(context):
    context.doc = get_request(frappe.form_dict.name)
    context.form_dict = frappe.form_dict
    context.name = frappe.form_dict.name
    context.show_sidebar = True
    context.add_breadcrumbs = True
    return context


def get_request(name):
    # Return refill request, but only if it is for current customer
    primary_customer = get_session_primary_customer()


    doc = frappe.get_doc("Refill Request", name)
    print("-----------------------------\n\n\n\n\n", doc.customer, primary_customer, doc.items)
    if doc.customer != primary_customer:
        print("DNM")
        return None

    print("Match")
    return doc