import frappe

from frappe import _

from .helpers import get_session_customers, auth

from bnovate.bnovate.report.stored_cartridges.stored_cartridges import get_data

no_cache = 1

auth()

def get_context(context):
    # User can see cartridges from all the customer he manages
    managed_customers = get_session_customers()
    context.data = get_data(frappe._dict({"customer": managed_customers}))
    context.show_sidebar = True
    return context