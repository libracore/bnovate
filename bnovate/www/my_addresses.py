import frappe

from frappe import _

from .helpers import auth, get_addresses, get_countries, build_sidebar, fixed_billing_address


no_cache = 1


def get_context(context):
    auth(context)
    # User can see cartridges from all the customers he manages
    build_sidebar(context)

    billing_address = fixed_billing_address()
    addresses = [a for a in get_addresses() if a.name != billing_address]

    context.addresses = addresses
    context.fixed_billing_address = billing_address
    context.countries = get_countries()
    context.title = _("My Addresses")

    return context