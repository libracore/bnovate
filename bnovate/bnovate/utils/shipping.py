# -*- coding: utf-8 -*-
# Copyright (c) bNovate (Douglas Watson)
# For license information, please see license.txt
#
# Wrappers for DHL APIs
# -------------------------
#
#######################################################################

import frappe
import datetime

from json import JSONDecodeError
from requests import request
from requests.exceptions import HTTPError

from frappe import _
from frappe.model.mapper import get_mapped_doc

from bnovate.bnovate.utils.realtime import set_status, STATUS_DONE

READ, WRITE = "read", "write"
PICKUP, DELIVERY = "pickup", "delivery"


class DHLException(Exception):
    pass


class ProductNotFound(DHLException):
    """ Request product was not offered in API response """

class AddressError(DHLException):
    """ Error while validating postal adress """

class DropShipImpossible(DHLException):
    """ If delivery and billing country are different, for example"""

#######################
# HELPERS
#######################


def _auth(ptype=WRITE):
    return frappe.has_permission("Shipment", ptype, throw=True)


def _get_settings():
    return frappe.get_single("bNovate Settings")

def get_country_code(country):
    """ Return country code for country name """
    if not country:
        country = _get_settings().default_country_of_origin
    country_doc = frappe.get_doc("Country", country)
    return country_doc.code.upper()

def get_unit_code(uom):
    """ Return DHL unit code for given ERP unit.  """
    unit_map = {
        'Unit': 'PCS',
        'Meter': 'M',
        'Centimeter': '2GM',
        'Liter': 'L',
        'mL': '3L',
    }

    if uom in unit_map:
        return unit_map[uom]
    return 'X'  # 'unit not required'

#######################
# BASE API CONNECTIONS
#######################


def dhl_request(path, method='GET', params=None, body=None, settings=None, auth=True):
    """ Make request to DHL API.
     
    Raises a DHLException if request fails
    """
    if auth:
        _auth(READ if method == 'GET' else WRITE)
    if settings is None:
        settings = _get_settings()
    resp = request(
        method,
        "https://express.api.dhl.com/mydhlapi/test" + path,
        params=params,
        json=body,
        auth=(settings.dhl_api_key, settings.dhl_api_secret),
    )

    try:
        resp.raise_for_status()
    except HTTPError as e:
        try:
            data = frappe._dict(resp.json())
            if data.title:
                raise DHLException(
                    "<b>{0}</b><br>{1}<br>{2}<br>{3}".format(data.title, data.message, data.detail, data.additionalDetails))
        except TypeError:
            # We can't convert body to JSON, raise generic error
            pass

        raise DHLException(e)

    data = frappe._dict(resp.json())

    return data


def build_address(address_line1, address_line2, city, pincode, country):
    """ Return dict of address formatted for DHL API """
    address = {
                "addressLine1": address_line1,
                "addressLine2": address_line2,
                "cityName": city,
                "postalCode": pincode,
                "countryCode": get_country_code(country),
    }
    return frappe._dict({k: v for k, v in address.items() if v})


#######################
# WRAPPERS
#######################


def validate_address(address, address_type):
    """ Validates if DHL Express has got pickup/delivery capabilities at origin/destination

    address_type must be either 'pickup' or 'delivery'

    Returns GMT Timezone offset for the destination (str)
    """

    params = {
        "countryCode": address.countryCode,
        "postalCode": address.postalCode,
        "type": address_type,
    }

    resp = dhl_request(
        "/address-validate",
        params=params
    )

    try:
        return resp['address'][0]['serviceArea']['GMTOffset']
    except (KeyError, IndexError, TypeError) as e:
        raise AddressError("Could not read Timezone from address")



@frappe.whitelist()
def get_price(shipment_docname):
    """ Return price quote for a Shipment Doc. 

    Includes pickup and delivery date estimates.
    """

    settings = _get_settings()
    doc = frappe.get_doc("Shipment", shipment_docname)

    product_code = "P"
    local_product_code = "S"

    if doc.pickup_country == "Switzerland" and doc.delivery_country == "Switzerland":
        product_code = "N"
        local_product_code = "N"

        if len(doc.shipment_parcel) > 1:
            raise DHLException("Domestic shipments only allow one parcel.")

    pickup_datetime = datetime.datetime.combine(
        doc.pickup_date, datetime.time()) + doc.pickup_from

    body = {
        "productsAndServices": [{
            "productCode": product_code,  # Domestic standard
            "localProductCode": local_product_code,
        }],
        "customerDetails": {
            "shipperDetails": build_address(
                doc.pickup_address_line1,
                doc.pickup_address_line2,
                doc.pickup_city,
                doc.pickup_pincode,
                doc.pickup_country,
            ),
            "receiverDetails": build_address(
                doc.delivery_address_line1,
                doc.delivery_address_line2,
                doc.delivery_city,
                doc.delivery_pincode,
                doc.delivery_country,
            ),
        },
        "accounts": [{
            "typeCode": "shipper",
            "number": settings.dhl_export_account,
        }],
        "packages": [{
            "weight": p.weight,
            "dimensions": {
                "length": p.length,
                "width": p.width,
                "height": p.height,
            }
        } for p in doc.shipment_parcel],
        "plannedShippingDateAndTime": pickup_datetime.isoformat(),
        "isCustomsDeclarable": True,
        "unitOfMeasurement": "metric"
    }

    resp = dhl_request("/rates", 'POST', body=body, settings=settings)

    # Find matching product
    quote = next(
        (p for p in resp.products if p['productCode'] == product_code), None)
    if quote is None:
        raise ProductNotFound()

    return quote


@frappe.whitelist()
def create_shipment(shipment_docname, task_id=None):
    """ Create Shipment, receive shipping label and tracking number. 

    Set validate_only to True to check deliverability etc.
    
    """

    set_status({
        "progress": 0,
        "message": _("Initiating request..."),
    }, task_id)

    settings = _get_settings()
    doc = frappe.get_doc("Shipment", shipment_docname)

    if doc.delivery_country != doc.bill_country:
        raise DropShipImpossible(_("Delivery country must be the same as Bill country"))


    product_code = "P"
    local_product_code = "S"
    value_added_services = [{
                # Paperless trade
                "serviceCode": "WY",
    }]
    customs_declarable = True

    if doc.pickup_country == "Switzerland" and doc.delivery_country == "Switzerland":
        product_code = "N"
        local_product_code = "N"
        value_added_services = []
        customs_declarable = False

        # TODO: loop over parcels, one shipment per parcel, or create multiple shipments.
        if len(doc.shipment_parcel) > 1:
            raise DHLException("Domestic shipments only allow one parcel.")

    # Date and time can't be in the past, even by a second
    pickup_datetime = datetime.datetime.combine(doc.pickup_date, datetime.time()) + doc.pickup_from
    if pickup_datetime <= datetime.datetime.now():
        pickup_datetime = datetime.datetime.now() + datetime.timedelta(minutes=10)


    pickup_address = build_address(
        doc.pickup_address_line1,
        doc.pickup_address_line2,
        doc.pickup_city,
        doc.pickup_pincode,
        doc.pickup_country
    )
    delivery_address = build_address(
        doc.delivery_address_line1,
        doc.delivery_address_line2,
        doc.delivery_city,
        doc.delivery_pincode,
        doc.delivery_country,
    )
    bill_address = build_address(
        doc.bill_address_line1,
        doc.bill_address_line2,
        doc.bill_city,
        doc.bill_pincode,
        doc.bill_country,
    )

    pickup_registration = []
    if doc.pickup_tax_id:
        pickup_registration += [{
            "typeCode": "VAT",
            "number": doc.pickup_tax_id,
            "issuerCountryCode": pickup_address.countryCode,
        }]
    if doc.pickup_eori_number:
        pickup_registration += [{
            "typeCode": "EOR",
            "number": doc.pickup_eori_number,
            "issuerCountryCode": pickup_address.countryCode,
        }]

    delivery_registration = []
    if doc.delivery_tax_id:
        delivery_registration += [{
            "typeCode": "VAT",
            "number": doc.delivery_tax_id,
            "issuerCountryCode": delivery_address.countryCode,
        }]
    if doc.delivery_eori_number:
        delivery_registration += [{
            "typeCode": "EOR",
            "number": doc.delivery_eori_number,
            "issuerCountryCode": delivery_address.countryCode,
        }]

    bill_registration = []
    if doc.bill_tax_id:
        bill_registration += [{
            "typeCode": "VAT",
            "number": doc.bill_tax_id,
            "issuerCountryCode": bill_address.countryCode,
        }]
    if doc.bill_eori_number:
        bill_registration += [{
            "typeCode": "EOR",
            "number": doc.bill_eori_number,
            "issuerCountryCode": bill_address.countryCode,
        }]

    set_status({
        "progress": 10,
        "message": _("Checking addresses..."),
    }, task_id)

    # Might be off +- 1 hour if request and delivery straddle DST change, shouldn't be an issue
    pickup_gmt_offset = validate_address(pickup_address, PICKUP)
    validate_address(delivery_address, DELIVERY)
    validate_address(bill_address, DELIVERY)

    # Commercial invoice no
    invoice_no = doc.name
    try:
        invoice_no = doc.shipment_delivery_note[0].delivery_note
    except IndexError:
        pass

    incoterm_place = doc.delivery_city
    if doc.incoterm in ('EXW', 'FCA'):
        incoterm_place = doc.pickup_city

    body = {
        "plannedShippingDateAndTime": "{0} GMT{1}".format(pickup_datetime.isoformat()[:19], pickup_gmt_offset),
        "pickup": {
            "isRequested": True,
            "closeTime": str(doc.pickup_to)[:5],
        },
        "productCode": product_code,
        "localProductCode": local_product_code,
        "accounts": [
            {
                "typeCode": "shipper",
                "number": settings.dhl_export_account,
            }
        ],
        "outputImageProperties": {
            "encodingFormat": "pdf",
            "imageOptions": [{
                    "typeCode": "label",
                    "templateName": "ECOM26_84_001"
                }, {
                    "templateName": "COMMERCIAL_INVOICE_03",
                    "invoiceType": "commercial",
                    "languageCode": "eng",
                    "isRequested": True,
                    "typeCode": "invoice"
            } ]
        },
        "customerDetails": {
            "shipperDetails": {
                "postalAddress": pickup_address,
                "contactInformation": {
                    "phone": doc.pickup_contact_phone,
                    "companyName": doc.pickup_company_name,
                    "fullName": doc.pickup_contact_display,
                    "email": doc.pickup_contact_email_rw,
                },
                "registrationNumbers": pickup_registration,
            },
            "receiverDetails": {
                "postalAddress": delivery_address,
                "contactInformation": {
                    "phone": doc.delivery_contact_phone,
                    "companyName": doc.delivery_company_name,
                    "fullName": doc.delivery_contact_display,
                    "email": doc.delivery_contact_email_rw,
                },
                "registrationNumbers": delivery_registration,
            },
            "buyerDetails": {
                "postalAddress": bill_address,
                "contactInformation": {
                    "phone": doc.bill_contact_phone,
                    "companyName": doc.bill_company_name,
                    "fullName": doc.bill_contact_display,
                    "email": doc.bill_contact_email_rw,
                },
                "registrationNumbers": bill_registration,
            }
        },
        "customerReferences": [
            {
                "value": invoice_no,
                "typeCode": "CU",
            },
            {
                "value": "TODO CUSTOMER PO NUMBER",
                "typeCode": "CO", # "buyers order number"
            },
            {
                "value": "TODO CUSTOMER PO NUMBER",
                "typeCode": "AAO",  # "shipment reference number of receiver"
            }
        ],
        "content": {
            "packages": [{
                "weight": p.weight,
                "dimensions": {
                    "length": p.length,
                    "width": p.width,
                    "height": p.height,
                },

            } for p in doc.shipment_parcel],
            "isCustomsDeclarable": customs_declarable,
            "description": doc.description_of_content,
            "incoterm": doc.incoterm,
            "unitOfMeasurement": "metric",
            "declaredValue": doc.value_of_goods,
            "declaredValueCurrency": doc.value_currency,
            "exportDeclaration": {
                "lineItems": [{
                    "number": i.idx,
                    "commodityCodes": [{
                        "value": i.customs_tariff_number or settings.default_customs_tariff_number,
                        "typeCode": "outbound",
                    }],
                    "priceCurrency": i.currency,
                    "quantity": {
                        "value": round(i.qty), # Integer needed for PCS
                        "unitOfMeasurement": get_unit_code(i.uom),
                    },
                    "price": i.amount if i.amount > 0 else 1, # TODO find better
                    "description": i.item_name,
                    "weight": {
                        "netValue": i.total_weight,
                        "grossValue": i.total_weight,
                    },
                    "exportReasonType": "permanent", # TODO: implement other types
                    "manufacturerCountry": get_country_code(i.country_of_origin)
                } for i in doc.shipment_delivery_note if i.total_weight > 0 ],
                "invoice": {
                    "date": doc.pickup_date.isoformat(),
                    "number": invoice_no,
                },
                "placeOfIncoterm": incoterm_place,
            },
        },
        # "shipmentNotification": [
        #     {
        #         "typeCode": "email",
        #         "receiverId": "receiver@example.com",
        #         "languageCode": "eng",
        #     }
        # ],
        "valueAddedServices": value_added_services,
        "getRateEstimates": True,
    }

    print("\n\n\n================================\n\n\n")
    import pprint
    pprint.pprint(body, compact=True)
    print("\n\n\n================================\n\n\n")

    set_status({
        "progress": 40,
        "message": _("Declaring contents..."),
    }, task_id)
    resp = dhl_request("/shipments", 'POST', body=body, settings=settings)


    doc.db_set("carrier", "DHL")
    doc.db_set("awb_number", resp['shipmentTrackingNumber'])
    doc.db_set("tracking_url", resp['trackingUrl'])
    if 'cancelPickupUrl' in resp:
        doc.db_set("cancel_pickup_url", resp['cancelPickupUrl'])
    doc.db_set("status", "Booked")
    # TODO: track piece by piece?

    if 'shipmentCharges' in resp:
        estimate = next((c for c in resp['shipmentCharges'] if 'priceCurrency' in c and c['priceCurrency'] == 'CHF'), None)
        if estimate is not None and 'price' in estimate:
            doc.db_set('shipment_amount', estimate['price'])

    set_status({
        "progress": 80,
        "message": _("Getting documents..."),
    }, task_id)

    for i, dhl_doc in enumerate(resp['documents']):
        frappe.utils.file_manager.save_file(
            "{0}-{1}-{2}.{3}".format(doc.name, dhl_doc['typeCode'], i, dhl_doc['imageFormat'].lower()),
            dhl_doc['content'],
            doc.doctype,
            doc.name,
            decode=True,
            is_private=1,
        )

    set_status({
        "progress": 100,
        "message": _("Done"),
    }, task_id, STATUS_DONE)

    return resp


#######################################
# Create Shipment from DN
#######################################

@frappe.whitelist()
def make_shipment_from_dn(source_name, target_doc=None):
    """ To be called from open_mapped_doc. """
    settings = _get_settings()
    def postprocess(source, target):
        # TODO change to sales admin
        user = frappe.db.get_value("User", frappe.session.user, ['email', 'full_name', 'phone', 'mobile_no'], as_dict=1)
        target.pickup_contact_email = user.email
        pickup_contact_display = '{}'.format(user.full_name)
        if user:
            if user.email:
                pickup_contact_display += '<br>' + user.email
            if user.phone:
                pickup_contact_display += '<br>' + user.phone
            if user.mobile_no and not user.phone:
                pickup_contact_display += '<br>' + user.mobile_no
        target.pickup_contact = pickup_contact_display

        # As we are using session user details in the pickup_contact then pickup_contact_person will be session user
        target.pickup_contact_person = frappe.session.user

        contact = frappe.db.get_value("Contact", source.contact_person, ['email_id', 'phone', 'mobile_no'], as_dict=1)
        delivery_contact_display = '{}'.format(source.contact_display)
        if contact:
            if contact.email_id:
                delivery_contact_display += '<br>' + contact.email_id
            if contact.phone:
                delivery_contact_display += '<br>' + contact.phone
            if contact.mobile_no and not contact.phone:
                delivery_contact_display += '<br>' + contact.mobile_no
        target.delivery_contact = delivery_contact_display

        if source.shipping_address_name:
            target.delivery_address_name = source.shipping_address_name
            target.delivery_address = source.shipping_address
        elif source.customer_address:
            target.delivery_address_name = source.customer_address
            target.delivery_address = source.address_display

        # Customisations
        target.bill_customer = source.customer

        for row in target.shipment_delivery_note:
            row.currency = source.currency
        
        target.pickup_from = settings.pickup_from  # Time is set to "now" somehow.
        target.pickup_to = settings.pickup_to

    doclist = get_mapped_doc("Delivery Note", source_name, {
        "Delivery Note": {
            "doctype": "Shipment",
            "field_map": {
                "grand_total": "value_of_goods",
                "currency": "value_currency",
                "company": "pickup_company",
                "company_address": "pickup_address_name",
                "company_address_display": "pickup_address",
                "customer": "delivery_customer",
                "contact_person": "delivery_contact_name",
                "contact_email": "delivery_contact_email",

                "customer_address": "bill_address_name",
                "posting_date": "pickup_date",
            },
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Delivery Note Item": {
            "doctype": "Shipment Delivery Note",
            "field_map": {
                "name": "dn_detail",
                "parent": "prevdoc_docname",
                "base_amount": "grand_total",
            }
        }
    }, target_doc, postprocess)

    return doclist