# Show list of all refill requests for that customer
# user can only place requests for his main Customer account, even if he manages 
# several.

import frappe

from frappe import _

from .helpers import get_session_primary_customer, auth

no_cache = 1

auth()

def get_context(context):
    context.data = get_requests()
    print("---------------------\n\n\n", context.data)
    context.show_sidebar = True
    return context

def get_requests():
    primary_customer = get_session_primary_customer()

    return frappe.get_all("Refill Request", 
        filters={
            "customer": ["=", primary_customer],
        },
        fields="*"
    )

