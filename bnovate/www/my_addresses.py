import frappe

from frappe import _

from .helpers import auth, get_addresses, get_countries, build_sidebar


no_cache = 1


def get_context(context):
    auth(context)
    # User can see cartridges from all the customers he manages
    build_sidebar(context)
    context.addresses = get_addresses()
    context.countries = get_countries()
    context.title = _("My Addresses")


    print("\n\n\n============================================\n\n\n")
    print(len(context.addresses))
    for addr in context.addresses:
        print(addr.name)
    print("\n\n\n============================================\n\n\n")
    return context