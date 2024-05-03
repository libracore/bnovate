# Allow customer to schedule his pickup

import json
import datetime

import frappe
from frappe import _
from frappe.utils import today
from frappe.exceptions import DoesNotExistError
from frappe.contacts.doctype.address.address import get_address_display

from .helpers import auth, get_session_primary_customer, allow_unstored_cartridges
from bnovate.bnovate.utils.shipping import _get_price, _request_pickup, _cancel_pickup, DateUnavailableError

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
        context.pickup_date = frappe.utils.today()

        context.pickup_from = "10:15"
        context.pickup_to = "18:15"

    elif shipment_doc.status == 'Completed':
        context.pickup_status = SCHEDULED
        context.pickup_date = shipment_doc.pickup_date

        # Remember frappe returns times as time deltas...some effort required to convert to 08:00 string format
        context.pickup_from = str(datetime.datetime.combine(datetime.date.today(), datetime.time()) + shipment_doc.pickup_from)[-8:-3]
        context.pickup_to = str(datetime.datetime.combine(datetime.date.today(), datetime.time()) + shipment_doc.pickup_to )[-8:-3]

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
        frappe.throw(_("Not Permitted"), frappe.PermissionError)
    rr_doc.set_indicator()
    rr_doc.set_tracking_url()

    # get shipment info
    if rr_doc.shipment:
        shipment_doc = frappe.get_doc("Shipment", rr_doc.shipment)
    else:
        raise DoesNotExistError("Pickup is not possible at this time")

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

    # Checks permissions too
    doc, _ = get_request(name)

    if doc is None or doc.shipping_label is None:
        raise DoesNotExistError()

    file_doc = frappe.get_doc("File", {"file_url": doc.shipping_label})

    frappe.local.response.filename = "shipping_label_{name}.pdf".format(name=name)
    frappe.local.response.filecontent = file_doc.get_content()
    frappe.local.response.type = "pdf"


@frappe.whitelist()
def get_pickup_capabilities(name, date=None, iterations=0):
    """ Get pickup capabilities for a refill request """

    if iterations > 20:
        frappe.throw(_("Could not find any pickup dates"))

    # Checks permissions too
    rr_doc, shipment_doc = get_request(name)

    if date == None:
        # First iteration: we want to check if pickup is possible now
        date = datetime.datetime.now()

    # Iteratively try dates until we get a valid one
    try:
        quote = _get_price(shipment_doc.name, pickup_datetime=date, auth=False)
    except DateUnavailableError:
        if iterations == 0:
            # Reset time to 00:00
            date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        return get_pickup_capabilities(name,  date + datetime.timedelta(days=1), iterations + 1)

    if 'pickupCapabilities' not in quote:
        frappe.throw(_("No Pickup Possible"))


    pickup_capabilities = quote['pickupCapabilities']

    # If we are within X minutes or passed the cutoff, try tomorrow:
    cutoff_datetime = datetime.datetime.fromisoformat(pickup_capabilities['localCutoffDateAndTime'])
    if datetime.datetime.now() + datetime.timedelta(minutes=10) >= cutoff_datetime:
        return get_pickup_capabilities(name, date + datetime.timedelta(days=1), iterations + 1)

    pickup_capabilities['pickupDate'] = date
    return pickup_capabilities

@frappe.whitelist()
def request_pickup(name, pickup_date, pickup_from, pickup_to, pickup_comment):
    """ Request pickup with DHL """

    # Checks permissions as well
    _, shipment_doc = get_request(name)

    shipment_doc.db_set('pickup_date', pickup_date)
    shipment_doc.db_set('pickup_from', pickup_from)
    shipment_doc.db_set('pickup_to', pickup_to)
    shipment_doc.db_set('pickup_comment', pickup_comment)

    return _request_pickup(shipment_doc.name, auth=False)

@frappe.whitelist()
def cancel_pickup(name, reason):
    """ Cancel a pickup """

    # Checks permissions as well
    _, shipment_doc = get_request(name)

    return _cancel_pickup(shipment_doc.name, reason, auth=False)
