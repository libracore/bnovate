import frappe

from frappe import _
from frappe.exceptions import DoesNotExistError

from .helpers import auth, get_session_customers, get_addresses, build_sidebar, has_cartridge_portal, \
    allow_unstored_cartridges, organize_return

from bnovate.bnovate.report.enclosure_filling_history import enclosure_filling_history

no_cache = 1


def get_context(context):
    auth(context)
    # User can see cartridges from all the customers he manages

    serial_no = frappe.form_dict.serial_no

    data = get_cartridge_data(serial_no)
    context.serial_no = serial_no
    context.filling_history = data.filling_history

    build_sidebar(context)
    context.title = _("Cartridge " + serial_no)
    return context


def get_cartridge_data(serial_no):
    """ Return list of cartridges owned and portal parameters """
    data = frappe._dict({
        "filling_history": [],
    })

    # Only allow if cartridge is owned by one of the user's customers
    managed_customers = [c.docname for c in get_session_customers()]
    sn_doc = frappe.get_doc("Serial No", serial_no)
    if sn_doc.owned_by not in managed_customers:
        raise DoesNotExistError


    if has_cartridge_portal():
        data.filling_history = enclosure_filling_history.get_data(frappe._dict({"serial_no": serial_no}))

    return data