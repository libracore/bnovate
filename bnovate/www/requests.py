# Show list of all refill requests for that customer
# user can only place requests for his main Customer account, even if he manages 
# several.

import frappe

from frappe import _

from bnovate.bnovate.doctype.refill_request.refill_request import RefillRequest

from .helpers import get_session_primary_customer, auth

no_cache = 1

auth()

def get_context(context):
    context.data = get_requests()
    context.show_sidebar = True
    context.title = _("Refill Requests")
    return context

def get_requests():
    primary_customer = get_session_primary_customer()

    docs = frappe.get_all("Refill Request", filters={
            "customer": ["=", primary_customer],
        },
        fields="*"
    )

    for doc in docs:
        RefillRequest.set_indicator(doc)

    return docs

