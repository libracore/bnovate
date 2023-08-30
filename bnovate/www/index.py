import frappe

from frappe import _

from .helpers import build_sidebar, is_guest, get_settings, has_cartridge_portal
from .instruments import get_instruments
from .requests import get_requests

from bnovate.bnovate.report.cartridge_status import cartridge_status

no_cache = 1

def get_context(context):
    # User can see cartridges from all the customers he manages
    context.is_guest = is_guest()
    if context.is_guest:
        context.greeting = get_settings().portal_home_page
        return context


    build_sidebar(context)
    context.title = _("Portal Home")

    # Quick connect
    context.connected_instruments = [ i for i in get_instruments() if i.cp ]

    # Cartridges
    context.has_cartridge_portal = has_cartridge_portal()
    context.requests = get_requests()


    return context
