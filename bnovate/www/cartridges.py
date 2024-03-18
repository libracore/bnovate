import frappe

from frappe import _

from .helpers import auth, get_session_customers, get_addresses, build_sidebar, has_cartridge_portal, allow_unstored_cartridges

from bnovate.bnovate.report.cartridge_status import cartridge_status

no_cache = 1


def get_context(context):
    auth(context)
    # User can see cartridges from all the customers he manages
    data = get_cartridges()
    context.cartridges = data.cartridges
    context.allow_unstored_cartridges = data.allow_unstored_cartridges

    build_sidebar(context)
    context.addresses = get_addresses()
    context.title = _("My Cartridges")
    return context


@frappe.whitelist()
def get_cartridges():
    """ Return list of cartridges owned and portal parameters """
    data = frappe._dict({
        "cartridges": [],
        "allow_unstored_cartridges": False,
    })

    managed_customers = [c.docname for c in get_session_customers()]
    if has_cartridge_portal() and managed_customers:
        data.cartridges = cartridge_status.get_data(frappe._dict({"customer": managed_customers}))
        data.allow_unstored_cartridges = allow_unstored_cartridges()

    return data