import frappe

from frappe import _
from frappe.exceptions import DoesNotExistError
from jinja2.filters import do_striptags


from .helpers import auth, get_session_customers, build_sidebar, is_service_partner

from bnovate.bnovate.utils import truncate, trim
from bnovate.bnovate.report.enclosure_filling_history import enclosure_filling_history
from bnovate.bnovate.report.service_history import service_history

no_cache = 1


def get_context(context):
    auth(context)
    # User can see cartridges from all the customers he manages

    serial_no = frappe.form_dict.serial_no

    data = get_instrument_data(serial_no)
    context.serial_no = serial_no
    context.service_history = data.service_history

    context.add_breadcrumbs = True
    context.parents = [
		{ "name": _("Instruments"), "route": "/instruments" },
	]

    build_sidebar(context)
    context.title = _("Instrument " + serial_no)
    return context


def get_instrument_data(serial_no):
    """ Return service history for an instrument """
    data = frappe._dict({
        "service_history": [],
    })

    # Only allow if cartridge is owned by one of the user's customers
    managed_customers = [c.docname for c in get_session_customers()]
    sn_doc = frappe.get_doc("Serial No", serial_no)
    if sn_doc.owned_by not in managed_customers:
        raise DoesNotExistError

    data.service_history = service_history.get_data(frappe._dict({"serial_no": serial_no}))

    for sr in data.service_history:
        sr.report_url = '/api/method/frappe.utils.print_format.download_pdf?' \
                + 'doctype=Service%20Report' \
                + '&name=' + sr.report \
                + '&format=Service%20Report' \
                + '&no_letterhead=0' \
                + '&_lang=' + 'en' 

    return data

@frappe.whitelist()
def get_service_report(report_no):
    """ Return PDF of analysis certificate for a given **fill** serial_no """

    managed_customers = [c.docname for c in get_session_customers()]

    # This also works if we feed the fill serial_no

    service_report = frappe.get_doc("Service Report", report_no)
    
    # If user doesn't own this instrument, he shouldn't even know if report exists. Same error either way:
    if not service_report or service_report.customer not in managed_customers:
        raise DoesNotExistError

    # TODO: return PDF. How to allow downloading of service report under same conditions as 
    # Return PDF
    # file_doc = frappe.get_doc("File", {"file_url": row.analysis_certificate})
    # frappe.local.response.filename = "analysis_certificate_{name}.pdf".format(name=serial_no)
    # frappe.local.response.filecontent = file_doc.get_content()
    # frappe.local.response.type = "pdf"
