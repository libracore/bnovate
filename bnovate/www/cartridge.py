import frappe

from frappe import _
from frappe.exceptions import DoesNotExistError
from jinja2.filters import do_striptags


from .helpers import auth, get_session_customers, get_addresses, build_sidebar, has_cartridge_portal, \
    allow_unstored_cartridges, organize_return

from bnovate.bnovate.utils import truncate, trim
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
    """ Return list of fillings for a **cartridge** serial_no """
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

    for row in data.filling_history:
        # analysis_certificate file is private, write a wrapper method to check permissions before allowing download
        if row.analysis_certificate:
            row.certificate_url = "/api/method/bnovate.www.cartridge.get_certificate?serial_no={serial_no}".format(serial_no=row.fill_serial)
        row.address_short = trim(row.shipping_address, "<br>", 20)

    return data


@frappe.whitelist()
def get_certificate(serial_no):
    """ Return PDF of analysis certificate for a given **fill** serial_no """

    managed_customers = [c.docname for c in get_session_customers()]

    # This also works if we feed the fill serial_no
    filling_history = enclosure_filling_history.get_data(frappe._dict({"serial_no": serial_no}))
    
    # If user doesn't own this cartridge, he shouldn't even know if it exists. Same error either way:
    if not filling_history or filling_history[0].owned_by not in managed_customers:
        raise DoesNotExistError

    row = filling_history[0]

    if not row.analysis_certificate:
        raise DoesNotExistError("No certificate found for this SN")

    # Return PDF
    file_doc = frappe.get_doc("File", {"file_url": row.analysis_certificate})
    frappe.local.response.filename = "analysis_certificate_{name}.pdf".format(name=serial_no)
    frappe.local.response.filecontent = file_doc.get_content()
    frappe.local.response.type = "pdf"
