import frappe

from frappe import _

from .helpers import auth, get_session_customers, get_addresses, get_countries

from bnovate.bnovate.report.cartridge_status import cartridge_status

no_cache = 1

auth()

def get_context(context):
    # User can see cartridges from all the customers he manages
    context.addresses = get_addresses()
    context.countries = get_countries()
    context.show_sidebar = True
    context.title = _("My Addresses")
    return context