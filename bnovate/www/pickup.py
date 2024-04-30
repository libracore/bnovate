# Allow customer to schedule his pickup

import json
import frappe

from frappe import _
from frappe.utils import today
from frappe.exceptions import DoesNotExistError

from .helpers import auth, get_session_primary_customer, get_session_contact, get_addresses, allow_unstored_cartridges

no_cache = 1

AVAILABLE, SCHEDULED = 'available', 'scheduled'


def get_context(context):
    auth(context)
    docname = frappe.form_dict.name 
    rr_doc, shipment_doc = get_request(docname) 

    context.AVAILABLE, context.SCHEDULED = AVAILABLE, SCHEDULED

    context.rr_doc = rr_doc
    context.shipment_doc = shipment_doc

    context.allow_unstored_cartridges = allow_unstored_cartridges()

    if rr_doc.shipping_label:
        context.shipping_label_url = "/api/method/bnovate.www.request.get_label?name={name}".format(name=docname)

    context.pickup_status = None
    if shipment_doc.status == 'Registered':
        context.pickup_status = AVAILABLE
    elif shipment_doc.status == 'Completed':
        context.pickup_status = SCHEDULED
        context.pickup_date = shipment_doc.pickup_date

    context.form_dict = frappe.form_dict
    context.name = docname
    context.show_sidebar = True
    context.add_breadcrumbs = True
    context.parents = [
		{ "name": _("Refill Requests"), "route": "/requests" },
		{ "name": docname, "route": "/requests/{0}".format(docname) },
	]
    context.title = _("Schedule Pickup")
    return context


def get_request(name):
    # Return refill request, but only if it is for current customer
    primary_customer = get_session_primary_customer()


    rr_doc = frappe.get_doc("Refill Request", name)
    if rr_doc.customer != primary_customer.docname:
        return None
    rr_doc.set_indicator()
    rr_doc.set_tracking_url()

    # get shipment info
    if rr_doc.shipment:
        shipment_doc = frappe.get_doc("Shipment", rr_doc.shipment)

    return rr_doc, shipment_doc

@frappe.whitelist()
def get_label(name):
    """ Return shipping label for this Refill Request """
    doc = get_request(name)

    if doc is None or doc.shipping_label is None:
        raise DoesNotExistError()

    file_doc = frappe.get_doc("File", {"file_url": doc.shipping_label})

    frappe.local.response.filename = "shipping_label_{name}.pdf".format(name=name)
    frappe.local.response.filecontent = file_doc.get_content()
    frappe.local.response.type = "pdf"

