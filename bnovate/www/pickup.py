# Allow customer to schedule his pickup

import json
import frappe

from frappe import _
from frappe.utils import today
from frappe.exceptions import DoesNotExistError

from .helpers import auth, get_session_primary_customer, allow_unstored_cartridges
from frappe.contacts.doctype.address.address import get_address_display

no_cache = 1

AVAILABLE, SCHEDULED = 'available', 'scheduled'


def get_context(context):
    auth(context)
    docname = frappe.form_dict.name 
    rr_doc, shipment_doc = get_request(docname) 

    context.AVAILABLE, context.SCHEDULED = AVAILABLE, SCHEDULED

    context.rr_doc = rr_doc
    context.shipment_doc = shipment_doc
    context.pickup_address_display = build_address_display(shipment_doc)
    context.parcel_count = len(shipment_doc.shipment_parcel)

    context.allow_unstored_cartridges = allow_unstored_cartridges()

    if rr_doc.shipping_label:
        context.shipping_label_url = "/api/method/bnovate.www.request.get_label?name={name}".format(name=docname)

    context.pickup_status = None
    if shipment_doc.status == 'Registered':
        context.pickup_status = AVAILABLE
    elif shipment_doc.status == 'Completed':
        context.pickup_status = SCHEDULED
        context.pickup_date = shipment_doc.pickup_date
    context.today = frappe.utils.today()
    context.min_time = "10:15"
    context.max_time = "18:15"

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

def build_address_display(shipment_doc):
    """ Return formatted address for display, matching exact values of shipment """
    return get_address_display({
        "contact_name": shipment_doc.pickup_contact_display,
        "company_name": shipment_doc.pickup_company_name,
        "address_line1": shipment_doc.pickup_address_line1,
        "address_line2": shipment_doc.pickup_address_line2,
        "pincode": shipment_doc.pickup_pincode,
        "city": shipment_doc.pickup_city,
        "country": shipment_doc.pickup_country,
        "phone": shipment_doc.pickup_contact_phone,
        "email_id": shipment_doc.pickup_contact_email_rw,
    })

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

