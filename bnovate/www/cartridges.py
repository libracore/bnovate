import frappe

from frappe import _

from .helpers import auth, get_session_customers, get_addresses

from bnovate.bnovate.report.cartridge_status import cartridge_status

no_cache = 1

auth()

def get_context(context):
    # User can see cartridges from all the customers he manages
    managed_customers = get_session_customers()
    context.data = cartridge_status.get_data(frappe._dict({"customer": managed_customers}))
    context.addresses = get_addresses()
    context.show_sidebar = True
    context.title = _("My Cartridges")
    return context