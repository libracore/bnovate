# Show list of all refill requests for that customer
# user can only place requests for his main Customer account, even if he manages 
# several.

import frappe

from frappe import _

from bnovate.bnovate.doctype.refill_request.refill_request import RefillRequest

from .helpers import get_session_primary_customer, auth, build_sidebar, has_cartridge_portal

no_cache = 1


def get_context(context):
    auth(context)
    build_sidebar(context)
    
    if has_cartridge_portal():
        context.data = get_requests()
    else:
        context.data = []
    context.title = _("Refill Requests")
    return context

def get_requests():

    primary_customer = get_session_primary_customer()
    docs = frappe.get_all("Refill Request", filters={
            "customer": ["=", primary_customer.docname],
        },
        fields="*"
    )

    for doc in docs:
        RefillRequest.set_indicator(doc)
        RefillRequest.set_tracking_url(doc)

    return docs

