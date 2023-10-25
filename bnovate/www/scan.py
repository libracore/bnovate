""" Scan status of multiple connected instruments """

from itertools import chain

from frappe import _

from .helpers import get_session_customers, auth, build_sidebar
from .instruments import get_instruments

no_cache = 1

def get_context(context):
    auth()

    context.customers = sorted(get_session_customers(), key=lambda c: c.customer_name)
    instruments = list(chain(*get_instruments(context.customers).values()))
    context.connected_instruments = [ i for i in instruments if i.cp ]

    context.title = _("Health Scan")
    # build_sidebar(context)
    context.add_breadcrumbs = True
    context.parents = [
		{ "name": _("Instruments"), "route": "/instruments" },
	]
    return context