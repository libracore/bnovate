import frappe

from frappe import _

from .helpers import auth, get_session_customers, get_addresses, build_sidebar, has_cartridge_portal

from bnovate.bnovate.report.cartridge_status import cartridge_status

no_cache = 1


def get_context(context):
    auth(context)
    # User can see cartridges from all the customers he manages
    managed_customers = [c.docname for c in get_session_customers()]
    if has_cartridge_portal() and managed_customers:
        context.data = cartridge_status.get_data(frappe._dict({"customer": managed_customers}))
    else:
        context.data = []

    build_sidebar(context)
    context.addresses = get_addresses()
    context.title = _("My Cartridges")
    return context