# Show data from a single request

import json
import frappe

from frappe import _
from frappe.utils import today

from .helpers import auth, get_session_primary_customer, get_session_contact, get_addresses

no_cache = 1

auth()

def get_context(context):
    context.doc = get_request(frappe.form_dict.name)
    context.form_dict = frappe.form_dict
    context.name = frappe.form_dict.name
    context.show_sidebar = True
    context.add_breadcrumbs = False
    return context


def get_request(name):
    # Return refill request, but only if it is for current customer
    primary_customer = get_session_primary_customer()


    doc = frappe.get_doc("Refill Request", name)
    if doc.customer != primary_customer.customer_name:
        return None
    doc.set_indicator()
    return doc


@frappe.whitelist()
def make_request(doc):
    """ Create a refill request """

    doc = frappe._dict(json.loads(doc))

    # Check that user does own the addresses
    valid_names = [a.name for a in get_addresses()]
    if not doc['shipping_address'] in valid_names:
        frappe.throw(_("You cannot order to this shipping address"), frappe.PermissionError)
    if not doc['billing_address'] in valid_names:
        frappe.throw(_("You cannot order to this billing address"), frappe.PermissionError)


    new_request = frappe.get_doc({
        'doctype': 'Refill Request',
        'customer': get_session_primary_customer().customer_name,
        'contact_person': get_session_contact(),
        'transaction_date': today(),
        'shipping_address': doc['shipping_address'],
        'billing_address': doc['billing_address'],
        'shipping_address_display': doc['shipping_address_display'],
        'billing_address_display': doc['billing_address_display'],
        'items': doc['items'],  # using data.items calls the built-in dict function...
        'remarks': doc['remarks'],
        'language': frappe.session.data.lang,
        'docstatus': 1,
    })

    new_request.insert(ignore_permissions=True)
    frappe.db.commit()

    return new_request