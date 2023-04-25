# Show data from a single request

import json
import frappe

from frappe import _

from .helpers import auth, get_session_primary_customer, get_session_contact

no_cache = 1

auth()

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
    if doc.customer != primary_customer:
        return None
    doc.set_indicator()
    return doc


@frappe.whitelist()
def make_request(doc):
    """ Create a refill request """

    # TODO: Check that items have a serial number and type
    # TODO: Check that user owns those addresses.
    # TODO: check that no open requests exist for those cartridges?

    doc = frappe._dict(json.loads(doc))

    new_request = frappe.get_doc({
        'doctype': 'Refill Request',
        'customer': get_session_primary_customer(),
        'contact_person': get_session_contact(),
        'shipping_address': doc['shipping_address'],
        'billing_address': doc['billing_address'],
        'shipping_address_display': doc['shipping_address_display'],
        'billing_address_display': doc['billing_address_display'],
        'items': doc['items'],  # using data.items calls the built-in dict function...
        'remarks': doc['remarks'],
        'docstatus': 1,
    })

    new_request.insert(ignore_permissions=True)
    frappe.db.commit()

    return new_request