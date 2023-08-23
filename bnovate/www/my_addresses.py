import frappe

from frappe import _

from .helpers import auth, get_addresses, get_countries, build_sidebar


no_cache = 1

auth()

def get_context(context):
    # User can see cartridges from all the customers he manages
    build_sidebar(context)
    context.addresses = get_addresses()
    context.countries = get_countries()
    context.title = _("My Addresses")
    return context