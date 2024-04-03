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

from frappe import _
from requests import request
from requests.exceptions import HTTPError

READ, WRITE = "read", "write"
PICKUP, DELIVERY = "pickup", "delivery"


class DHLException(Exception):
    pass


class ProductNotFound(DHLException):
    """ Request product was not offered in API response """

class AddressError(DHLException):
    """ Error while validating postal adress """

#######################
# HELPERS
#######################


def _auth(ptype=WRITE):
    return frappe.has_permission("Shipment", ptype, throw=True)


def _get_settings():
    return frappe.get_single("bNovate Settings")

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
        print(str(e))

        try:
            data = frappe._dict(resp.json())
            if data.title:
                print(data)
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

    country_doc = frappe.get_doc("Country", country)

    address = {
                "addressLine1": address_line1,
                "addressLine2": address_line2,
                "cityName": city,
                "postalCode": pincode,
                "countryCode": country_doc.code.upper(),
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

    print(resp)

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

    # FIXME? Not specifying timezone, hopefully will use TZ from pickup address
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
def create_shipment(shipment_docname):
    """ Create Shipment, receive shipping label and tracking number """

    settings = _get_settings()
    doc = frappe.get_doc("Shipment", shipment_docname)

    product_code = "P"
    local_product_code = "S"
    value_added_services = [{
                # Paperless trade
                "serviceCode": "WY",
    }]

    if doc.pickup_country == "Switzerland" and doc.delivery_country == "Switzerland":
        product_code = "N"
        local_product_code = "N"
        value_added_services = []

        # TODO: loop over parcels, one shipment per parcel, or create multiple shipments.
        if len(doc.shipment_parcel) > 1:
            raise DHLException("Domestic shipments only allow one parcel.")

    pickup_datetime = datetime.datetime.combine(doc.pickup_date, datetime.time()) + doc.pickup_from

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

    # Might be off +- 1 hour if request and delivery straddle DST change, shouldn't be an issue
    pickup_gmt_offset = validate_address(pickup_address, PICKUP)
    validate_address(delivery_address, DELIVERY)

    body = {
        "plannedShippingDateAndTime": "{0} GMT{1}".format(pickup_datetime.isoformat(), pickup_gmt_offset),
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
            "imageOptions": [
                {
                    "typeCode": "label",
                    "templateName": "ECOM26_84_001"
                },
            ]
        },
        "customerDetails": {
            "shipperDetails": {
                "postalAddress": pickup_address,
                "contactInformation": {
                    "phone": doc.pickup_contact_phone,
                    "companyName": doc.pickup_company_name,
                    "fullName": doc.pickup_contact_display,
                    "email": doc.pickup_contact_email,
                }
            },
            "receiverDetails": {
                "postalAddress": delivery_address,
                "contactInformation": {
                    "phone": doc.delivery_contact_phone,
                    "companyName": doc.delivery_company_name,
                    "fullName": doc.delivery_contact_display,
                    "email": doc.delivery_contact_email,
                }
            }
        },
        "customerReferences": [
            {
                "value": "TODO DN-12335-Test2",
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
            "isCustomsDeclarable": False,
            "description": doc.description_of_content,
            "incoterm": doc.incoterm,
            "unitOfMeasurement": "metric",
        },
        "shipmentNotification": [
            {
                "typeCode": "email",
                "receiverId": "douglas.watson+api_stuff@bnovate.com",
                "languageCode": "eng",
            }
        ],
        "valueAddedServices": value_added_services,
    }

    print("\n\n\n================================\n\n\n")
    print(body)
    print("\n\n\n================================\n\n\n")

    resp = dhl_request("/shipments", 'POST', body=body, settings=settings)


    doc.db_set("carrier", "DHL")
    doc.db_set("awb_number", resp['shipmentTrackingNumber'])
    doc.db_set("tracking_url", resp['trackingUrl'])
    if 'cancelPickupUrl' in resp:
        doc.db_set("cancel_pickup_url", resp['cancelPickupUrl'])
    doc.db_set("status", "Booked")
    # TODO: track piece by piece?

    for i, dhl_doc in enumerate(resp['documents']):
        frappe.utils.file_manager.save_file(
            "{0}-{1}-{2}.{3}".format(doc.name, dhl_doc['typeCode'], i, dhl_doc['imageFormat'].lower()),
            dhl_doc['content'],
            doc.doctype,
            doc.name,
            decode=True,
            is_private=1,
            df="shipping_label",  # TODO: how will this work with multiple shipments?
        )

    return resp
