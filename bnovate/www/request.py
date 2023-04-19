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
    return doc


@frappe.whitelist()
def make_request(data):
    """ Create a refill request """

    # TODO: Check that items have a serial number and type
    data = frappe._dict(json.loads(data))

    print("--------------\n\n", type(data), data, frappe.session)

    new_request = frappe.get_doc({
        'doctype': 'Refill Request',
        'customer': get_session_primary_customer(),
        'contact': get_session_contact(),
        'items': data['items'],  # using data.items calls the built-in dict function...
    })

    print(new_request)
    print(new_request.meta.get_table_fields())
    fieldname = new_request.meta.get_table_fields()[0].fieldname
    print(fieldname)
    print(new_request.get(fieldname))

    new_request.insert(ignore_permissions=True)
    frappe.db.commit()