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
import itertools

from json import JSONDecodeError
from requests import request
from requests.exceptions import HTTPError

from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.contacts.doctype.contact.contact import get_contact_details

from bnovate.bnovate.utils.realtime import set_status, STATUS_DONE

READ, WRITE = "read", "write"
PICKUP, DELIVERY = "pickup", "delivery"


class DHLException(Exception):
    pass

class DHLBadRequestError(DHLException):
    """ Missing or bad data in an API request """
    def __init__(self, title, message, detail, additional_details):
        self.title = title
        self.message = message
        self.detail = detail
        self.additional_details = additional_details

    def __str__(self):
        return self.to_html()

    def to_html(self):
        return "<b>{0}</b><br>{1}<br>{2}<br>{3}".format(self.title, self.message or "", self.detail or "", self.additional_details or "") 


class ProductNotFoundError(DHLException):
    """ Request product was not offered in API response """

class AddressError(DHLException):
    """ Error while validating postal adress """
    def __init__(self, message):
        self.message = message
    
    def __str__(self):
        return self.message

class MissingParcelError(DHLException):
    """ No parcels declared """

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

def get_export_reason_type(reason):
    """ Return DHL typecode for export reason """
    reason_lookup = {
        "Permanent": "permanent",
        "Temporary": "temporary",
        "Return": "return",
        "Used exhibition goods to origin": "used_exhibition_goods_to_origin",
        "Intercompany use": "intercompany_use",
        "Commercial purpose or sale": "commercial_purpose_or_sale",
        "Personal belongings or personal use": "personal_belongings_or_personal_use",
        "Sample": "sample",
        "Gift": "gift",
        "Return to origin": "return_to_origin",
        "Warranty replacement": "warranty_replacement",
        "Diplomatic goods": "diplomatic_goods",
        "Defence material": "defence_material",
    }

    if reason not in reason_lookup:
        return "permanent"
    else:
        return reason_lookup[reason]


@frappe.whitelist()
def get_default_times(pallets='No'):
    """ Return last possible of day to request same-day pickup """
    # Needed as a dedicated function to avoid fetching settings from front-end.
    settings = _get_settings()
    same_day_cutoff = settings.pallet_same_day_cutoff if pallets == 'Yes' else settings.same_day_cutoff
    return {
        "same_day_cutoff": same_day_cutoff,
        "pickup_from": settings.pickup_from,
        "pickup_to": settings.pickup_to,
    }


def strip(s):
    return s.strip() if type(s) == str else s

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

    base_url = "https://express.api.dhl.com/mydhlapi/test"
    if settings.use_live_api:
        base_url = "https://express.api.dhl.com/mydhlapi" 
    resp = request(
        method,
        base_url + path,
        params=params,
        json=body,
        auth=(settings.dhl_api_key, settings.dhl_api_secret),
    )

    try:
        resp.raise_for_status()
    except HTTPError as e:
        try:
            data = frappe._dict(resp.json())
            raise DHLBadRequestError(data.title, data.message, data.detail, data.additionalDetails)
        except TypeError:
            # We can't convert body to JSON, raise generic error
            pass

        raise DHLException(e)

    data = frappe._dict(resp.json())

    return data


def build_address(address_line1, address_line2, city, pincode, country):
    """ Return dict of address formatted for DHL API """
    address = {
        "addressLine1": strip(address_line1[:45] if address_line1 else None),
        "addressLine2": strip(address_line2[:45] if address_line2 else None),
        "cityName": strip(city),
        "postalCode": strip(pincode),
        "countryCode": strip(get_country_code(country)),
    }
    return frappe._dict({k: v for k, v in address.items() if v})


#######################
# WRAPPERS
#######################

def quick_validate_address(pincode, country):
    """ Validate deliverability of an address based on minimal params, for use with Portal.
     
    Raises AddressError if not valid, else is silent.
    """
    params = {
        "countryCode": get_country_code(country),
        "postalCode": pincode,
        "type": DELIVERY,
    }

    try:
        resp = dhl_request(
            "/address-validate",
            params=params,
            auth=False
        )
    except DHLBadRequestError as e:
        raise AddressError("Invalid Adddress. Check Postal Code.")

def validate_address(name):
    """ Validate an address for delivery. For now we only look at postal code and country """

    doc = frappe.get_doc("Address", name)
    address = build_address(doc.address_line1, doc.address_line2, doc.city, doc.pincode, doc.country)

    try:
        return _validate_address(address, DELIVERY)
    except AddressError:
        raise AddressError("Check Postal Code")

def _validate_address(address, address_type):
    """ Validates if DHL Express has got pickup/delivery capabilities at origin/destination

    address_type must be either 'pickup' or 'delivery'

    Returns GMT Timezone offset for the destination (str)
    """

    params = {
        "countryCode": address.countryCode,
        "postalCode": address.postalCode,
        "type": address_type,
    }

    try:
        resp = dhl_request(
            "/address-validate",
            params=params
        )
    except DHLBadRequestError as e:
        address_display = "{0} // {1} // {2} // {3}".format(address.addressLine1, address.addressLine2, address.postalCode, address.countryCode)
        raise AddressError("Could not validate address: '{0}'. Message: {1}".format(address_display, e.detail))

    try:
        return resp['address'][0]['serviceArea']['GMTOffset']
    except (KeyError, IndexError, TypeError) as e:
        raise DHLException("Could not read Timezone from address")



@frappe.whitelist()
def get_price(shipment_docname):
    """ Return price quote for a Shipment Doc. 

    Includes pickup and delivery date estimates.
    """

    settings = _get_settings()
    doc = frappe.get_doc("Shipment", shipment_docname)

    product_code = "P"
    accounts = [{
        "typeCode": "shipper",
        "number": settings.dhl_import_account if doc.is_return else settings.dhl_export_account, 
    }]

    if doc.pickup_country == "Switzerland" and doc.delivery_country == "Switzerland":
        product_code = "N"

        # Event returns use our standard 'export' account
        accounts = [{
            "typeCode": "shipper",
            "number": settings.dhl_export_account, 
        }]

        if len(doc.shipment_parcel) > 1:
            raise DHLException("Domestic shipments only allow one parcel.")

    pickup_datetime = datetime.datetime.combine(
        doc.pickup_date, datetime.time()) + doc.pickup_from

    body = {
        "productsAndServices": [{
            "productCode": product_code,
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
        "accounts": accounts,
        "packages": list(itertools.chain(*[[{
            "weight": p.weight,
            "dimensions": {
                "length": p.length,
                "width": p.width,
                "height": p.height,
            }, 
        }] * p.count for p in doc.shipment_parcel])),
        "plannedShippingDateAndTime": pickup_datetime.isoformat(),
        "isCustomsDeclarable": True,
        "unitOfMeasurement": "metric"
    }

    resp = dhl_request("/rates", 'POST', body=body, settings=settings)

    # Find matching product
    quote = next(
        (p for p in resp.products if p['productCode'] == product_code), None)
    if quote is None:
        raise ProductNotFoundError()

    return quote


@frappe.whitelist()
def create_shipment(shipment_docname, pickup=False, task_id=None):
    # Args are passed as text!
    pickup = bool(int(pickup))
    try:
        return _create_shipment(shipment_docname, pickup, task_id)
    except Exception as e:
        set_status({
            "progress": 100,
            "message": _("Error"),
        }, task_id, STATUS_DONE)

        raise e


def _create_shipment(shipment_docname, pickup=False, task_id=None):
    """ Create Shipment, receive shipping label and tracking number. 

    Set validate_only to True to check deliverability etc.
    
    """
    
    set_status({
        "progress": 0,
        "message": _("Initiating request..."),
    }, task_id)

    settings = _get_settings()
    doc = frappe.get_doc("Shipment", shipment_docname)

    if doc.status != "Submitted":
        raise DHLException("Can only create shipment if status is 'Submitted'")

    if len(doc.shipment_parcel) == 0:
        raise MissingParcelError(_("Please specify types of parcel"))
    if doc.delivery_country != doc.bill_country:
        raise DropShipImpossible(_("Delivery country must be the same as Bill country"))
    if doc.is_return and doc.delivery_country != "Switzerland":
        raise DHLException(_("Only returns to Switzerland are supported at this stage"))


    product_code = "P"
    customs_declarable = True
    value_added_services = [{
        "serviceCode": "WY", # Paperless trade
    }, {
        "serviceCode": "FD", # GOGREEN
    }]

    # In case of domestic shipment, accounts are reset later.
    accounts = [{
        "typeCode": "shipper",
        "number": settings.dhl_export_account, 
    }]

    if doc.incoterm == "DDP":
        accounts += [{
            "typeCode": "duties-taxes",
            "number": settings.dhl_export_account, 
        }]
    elif doc.is_return:
        accounts = [{
            "typeCode": "shipper",
            "number": settings.dhl_import_account, 
        }, {
            "typeCode": "duties-taxes",
            "number": settings.dhl_import_account, 
        }]

    label_format = "ECOM26_84_001"  # Matches DHL printer
    if doc.is_return:
        label_format = "ECOM26_84_A4_001"  # A4

    image_options = [{
            "typeCode": "label",
            "templateName": label_format
        }, {
            "templateName": "COMMERCIAL_INVOICE_03",
            "invoiceType": "commercial",
            "languageCode": "eng",
            "isRequested": True,
            "typeCode": "invoice"
    }] 

    if doc.pickup_country == "Switzerland" and doc.delivery_country == "Switzerland":
        product_code = "N"
        value_added_services = []
        customs_declarable = False

        image_options = [{
            "typeCode": "label",
            "templateName": label_format,
        }]

        # No import account, no duty paid, etc.
        accounts = [{
            "typeCode": "shipper",
            "number": settings.dhl_export_account, 
        }]

        # TODO: loop over parcels, one shipment per parcel, or create multiple shipments.
        if len(doc.shipment_parcel) > 1:
            raise DHLException("Domestic shipments only allow one parcel.")

    if doc.is_return:
        value_added_services += [{
            "serviceCode": "PT",  # 3 month data staging
        }]


    # Date and time can't be in the past, even by a second
    # Note that times in the doc are given as datetime.timedelta objects.
    pickup_datetime = datetime.datetime.combine(doc.pickup_date, datetime.time()) + doc.pickup_from
    if pickup_datetime <= datetime.datetime.now():
        pickup_datetime = datetime.datetime.now() + datetime.timedelta(minutes=10)
    close_time = (datetime.datetime.min + doc.pickup_to).time()


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
    pickup_gmt_offset = _validate_address(pickup_address, PICKUP)
    _validate_address(delivery_address, DELIVERY)
    _validate_address(bill_address, DELIVERY)

    # Commercial invoice data
    invoice_contact = frappe.get_doc("User", settings.shipping_contact)
    invoice_contact.full_name = ' '.join([invoice_contact.first_name, invoice_contact.last_name]).strip()
    invoice_no = doc.name
    if len(doc.items) >= 1:
        invoice_no = (
            doc.items[0].delivery_note
            or doc.items[0].sales_order 
            or doc.items[0].refill_request 
            or invoice_no
        )

    if doc.is_return:
        invoice_no += " RETURN"

    incoterm_place = doc.delivery_city
    if doc.incoterm in ('EXW', 'FCA'):
        incoterm_place = doc.pickup_city

    body = {
        "plannedShippingDateAndTime": "{0} GMT{1}".format(pickup_datetime.isoformat()[:19], pickup_gmt_offset),
        "pickup": {
            "isRequested": bool(pickup),
            "closeTime": close_time.isoformat()[:5],
            "specialInstructions": [{
                "value": doc.pickup_comment[:75],
            }] if doc.pickup_comment else [],
        },
        "productCode": product_code,
        "accounts": accounts,
        "outputImageProperties": {
            "encodingFormat": "pdf",
            "imageOptions": image_options,
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
        ],
        "content": {
            "packages": list(itertools.chain(*[[{
                    "weight": p.weight,
                    "dimensions": {
                        "length": p.length,
                        "width": p.width,
                        "height": p.height,
                    }, 
            }] * p.count for p in doc.shipment_parcel])),
            "isCustomsDeclarable": customs_declarable,
            "description": doc.description_of_content,
            "incoterm": doc.incoterm,
            "unitOfMeasurement": "metric",
            "declaredValue": doc.declared_value,
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
                    "price": i.rate if i.rate > 0 else 1, # TODO find better
                    "description": i.item_name,
                    "weight": {
                        "netValue": i.total_weight or 1.0,
                        "grossValue": i.total_weight or 1.0,
                    },
                    "exportReasonType": get_export_reason_type(doc.reason_for_export),
                    "manufacturerCountry": get_country_code(i.country_of_origin)
                } for i in doc.items],
                "recipientReference": doc.po_no,
                "invoice": {
                    "date": doc.pickup_date.isoformat(),
                    "number": invoice_no,
                    "signatureName": invoice_contact.full_name,
                },
                "additionalCharges": [{
                    "value": doc.shipment_amount,
                    "typeCode": "freight",
                }] if doc.shipment_amount else [],
                "placeOfIncoterm": incoterm_place,
            },
        },
        "valueAddedServices": value_added_services,
        "getRateEstimates": True,
    }

    print("\n\n\n================================\n\n\n")
    import json
    print(json.dumps(body, indent=2))
    print("\n\n\n================================\n\n\n")

    set_status({
        "progress": 40,
        "message": _("Declaring contents..."),
    }, task_id)
    resp = dhl_request("/shipments", 'POST', body=body, settings=settings)


    doc.db_set("carrier", "DHL")
    doc.db_set("awb_number", resp['shipmentTrackingNumber'])
    doc.db_set("pickup_confirmation_number", resp['dispatchConfirmationNumber'] if 'cancelPickupUrl' in resp else None)
    if pickup:
        doc.db_set("status", "Completed")
    else:
        doc.db_set("status", "Registered")
    # TODO: track piece by piece?

    if 'shipmentCharges' in resp:
        estimate = next((c for c in resp['shipmentCharges'] if 'priceCurrency' in c and c['priceCurrency'] == 'CHF'), None)
        if estimate is not None and 'price' in estimate:
            doc.db_set('shipment_cost', estimate['price'])

    set_status({
        "progress": 80,
        "message": _("Getting documents..."),
    }, task_id)

    for i, dhl_doc in enumerate(resp['documents']):
        df = None
        if dhl_doc['typeCode'] == "label":
            df = "shipping_label"
        elif dhl_doc['typeCode'] == "invoice":
            df = "commercial_invoice"

        file = frappe.utils.file_manager.save_file(
            "{0}-{1}-{2}.{3}".format(doc.name, dhl_doc['typeCode'], i, dhl_doc['imageFormat'].lower()),
            dhl_doc['content'],
            doc.doctype,
            doc.name,
            folder="Home",
            decode=True,
            is_private=1,
            df=df,
        )

        if df is not None:
            doc.db_set(df, file.file_url)

    set_status({
        "progress": 100,
        "message": _("Done"),
    }, task_id, STATUS_DONE)

    return resp


@frappe.whitelist()
def request_pickup(shipment_docname, task_id=None):
    try:
        return _request_pickup(shipment_docname, task_id=task_id)
    except Exception as e:
        set_status({
            "progress": 100,
            "message": _("Error"),
        }, task_id, STATUS_DONE)

        raise e

def _request_pickup(shipment_docname, task_id=None):
    """ Request pickup """
    
    doc = frappe.get_doc("Shipment", shipment_docname)
    settings = _get_settings()

    if doc.status != "Registered":
        raise DHLException("Can only request pickup if status is 'Registered'")

    accounts = [{
        "typeCode": "shipper",
        "number": settings.dhl_import_account if doc.is_return else settings.dhl_export_account, 
    }]

    product_code = "P"
    customs_declarable = True
    if doc.pickup_country == "Switzerland" and doc.delivery_country == "Switzerland":
        product_code = "N"
        customs_declarable = False

        accounts = [{
            "typeCode": "shipper",
            "number": settings.dhl_export_account, 
        }]

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
    pickup_gmt_offset = _validate_address(pickup_address, PICKUP)

    body = {
        "plannedPickupDateAndTime": "{0} GMT{1}".format(pickup_datetime.isoformat()[:19], pickup_gmt_offset),
        "accounts": accounts, 
        "specialInstructions": [{
            "value": doc.pickup_comment[:80],
        }] if doc.pickup_comment else [],
        "customerDetails": {
            "shipperDetails": {
                "postalAddress": pickup_address,
                "contactInformation": {
                    "phone": doc.pickup_contact_phone,
                    "companyName": doc.pickup_company_name,
                    "fullName": doc.pickup_contact_display,
                    "email": doc.pickup_contact_email_rw,
                },
            },
        },
        "shipmentDetails": [{
            "productCode": product_code,
            "packages": list(itertools.chain(*[[{
                    "weight": p.weight,
                    "dimensions": {
                        "length": p.length,
                        "width": p.width,
                        "height": p.height,
                    }, 
            }] * p.count for p in doc.shipment_parcel])),
            "isCustomsDeclarable": customs_declarable,
            "declaredValue": doc.declared_value,
            "declaredValueCurrency": doc.value_currency,
            "unitOfMeasurement": "metric",
            "shipmentTrackingNumber": doc.awb_number,
        }],
    }


    print("\n\n\n================================\n\n\n")
    import json
    print(json.dumps(body, indent=2))
    print("\n\n\n================================\n\n\n")


    set_status({
        "progress": 40,
        "message": _("Requesting pickup..."),
    }, task_id)

    resp = dhl_request("/pickups", 'POST', body=body, settings=settings)

    doc.db_set("status", "Completed")
    try:
        doc.db_set("pickup_confirmation_number", resp['dispatchConfirmationNumbers'][0])
    except (KeyError, IndexError, TypeError) as e:
        # Too bad, can't get  the dispatch number
        pass

    set_status({
        "progress": 100,
        "message": _("Done"),
    }, task_id, STATUS_DONE)

    return resp


@frappe.whitelist()
def cancel_pickup(shipment_docname, reason, task_id=None):
    """ Cancel a pickup request. Resets doc status to 'Registered' """
    try:
        return _cancel_pickup(shipment_docname, reason, task_id=task_id)
    except Exception as e:
        set_status({
            "progress": 100,
            "message": _("Error"),
        }, task_id, STATUS_DONE)

        raise e 

def _cancel_pickup(shipment_docname, reason, task_id=None):
    doc = frappe.get_doc("Shipment", shipment_docname)

    if not doc.pickup_confirmation_number:
        frappe.throw("This shipment does not have a Pickup Confirmation Number")
    

    set_status({
        "progress": 40,
        "message": _("Cancelling pickup..."),
    }, task_id)

    resp = dhl_request(
        "/pickups/{0}".format(doc.pickup_confirmation_number),
        "DELETE",
        params={
            "reason": reason,
            "requestorName": frappe.get_user().doc.full_name,
        }
    )

    doc.db_set('status', 'Registered')
    doc.db_set('pickup_confirmation_number', None)

    set_status({
        "progress": 100,
        "message": _("Done"),
    }, task_id, STATUS_DONE)

    return resp


#######################################
# EXTENSIONS TO SHIPMENT DOCTYPE
#######################################

@frappe.whitelist()
def parcel_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT 
            parcel_template_name, 
            CONCAT(length, "x", width, "x", height, ", ", ROUND(weight), " kg") as dimensions
        FROM `tabShipment Parcel Template`
        WHERE {key} LIKE %(txt)s
        ORDER BY parcel_template_name
        LIMIT %(start)s, %(page_len)s
    """.format(**{
            'key': searchfield,
        }), {
        'txt': "%{}%".format(txt),
        '_txt': txt.replace("%", ""),
        'start': start,
        'page_len': page_len
    })

@frappe.whitelist()
def set_pallets(doc, method=None):
    """ Set pallet vs non-pallet status.
     
    Called on lifecycle hooks on DN and Shipment (see hooks.py)
    """

    if method not in ('before_save'):
        return
    
    has_pallet = sum([p.is_pallet or 0 for p in doc.shipment_parcel], 0)
    doc.db_set('pallets', 'Yes' if has_pallet else 'No')

    if has_pallet and not doc.pickup_comment:
        doc.db_set('pickup_comment', _get_settings().pallet_pickup_comment)

    # Also clear template to avoid keeping that link around:
    doc.db_set('parcel_template', None)

@frappe.whitelist()
def set_totals(doc, method=None):
    """ Calculate total declared value (items + shipping). Called by hooks.py """
    for row in doc.items:
        if row.qty and row.rate:
            row.amount = row.qty * row.rate

    line_item_value = sum([r.amount or 0 for r in doc.items], 0)
    total = line_item_value + (doc.shipment_amount or 0)
    doc.declared_value = total

def set_missing_values(doc, method=None):
    """ Check all values before saving or submitting. Called by hooks.py """

    if doc.is_return:
        doc.incoterm = "DAP"

@frappe.whitelist()
def fill_address_data(address_type, address_name,  company=None, customer=None, supplier=None, contact=None, 
                      user=None, validate=False):
    """ Return address fields for given business / address / contact. 

    Fills as much data as possible from the address.

    Tax info is fetched from the business doctype (company, customer, or supplier).

    If missing from address:
    - company name is taken from business doctype
    - name, email, phone are taken from the person doctype (contact or user)

    If validate = True, raises AddressError if required fields are missing
    
    """

    if address_type not in ('pickup', 'delivery', 'bill'):
        raise ValueError("address_type must be one of ('pickup', 'delivery', 'bill')")

    if company:
        business_type = "Company"
        business_doc = frappe.get_doc("Company", company)
        business_doc.company_name = business_doc.name
    elif customer:
        business_type = "Customer"
        business_doc = frappe.get_doc("Customer", customer)
        business_doc.company_name = business_doc.customer_name
    elif supplier:
        business_type = "Supplier"
        business_doc = frappe.get_doc("Supplier", supplier)
        business_doc.company_name = business_doc.supplier_name
    else:
        raise ValueError("Please specify one of: company, customer, supplier")

    address_doc = frappe.get_doc("Address", address_name)

    if contact:
        contact_doc = frappe.get_value("Contact", contact, ['first_name', 'last_name', 'email_id', 'phone', 'mobile_no'], as_dict=True)
        contact_doc.contact_display = ' '.join([contact_doc.first_name, contact_doc.last_name]).strip()
        contact_doc.email = contact_doc.email_id
    elif user:
        contact_doc = frappe.get_value("User", user, ['full_name', 'email', 'phone', 'mobile_no'], as_dict=True)
        contact_doc.contact_display = contact_doc.full_name
    else:
        raise ValueError("Please specify one of: contact, user")
    contact_doc.phone = contact_doc.phone or contact_doc.mobile_no

    # DHL API doesn't support multiple emails, keep only the first one.
    def trim_email(email_id):
        return email_id.split(',')[0].strip()

    def val(field, msg):
        if validate_address and not fields[field]:
            raise AddressError(msg)

    fields = {
        address_type + "_company_name": strip(address_doc.company_name or business_doc.company_name),
        address_type + "_tax_id": strip(business_doc.tax_id),
        address_type + "_eori_number": strip(business_doc.eori_number),
        address_type + "_address_line1": strip(address_doc.address_line1),
        address_type + "_address_line2": strip(address_doc.address_line2),
        address_type + "_pincode": strip(address_doc.pincode),
        address_type + "_city": strip(address_doc.city),
        address_type + "_country": strip(address_doc.country),
        address_type + "_contact_display": strip(address_doc.contact_name or contact_doc.contact_display), 
        address_type + "_contact_email_rw": trim_email(address_doc.email_id or contact_doc.email or ''),
        address_type + "_contact_phone": strip(address_doc.phone or contact_doc.phone),
    }

    val(address_type + "_company_name", "Specify company name in the Address or {0}".format(business_type))
    val(address_type + "_tax_id", "Specify Tax ID in {0}".format(business_type))
    if (address_doc.country != "Switzerland"):
        val(address_type + "_eori_number", "Specify EORI number in {0}".format(business_type))
    val(address_type + "_address_line1", "Specify address line 1 in Address")
    val(address_type + "_pincode", "Specify Postal Code in Address")
    val(address_type + "_city", "Specify City in Address")
    val(address_type + "_country", "Specify Country in Address")
    val(address_type + "_contact_display", "Specify Contact Name in Address or a full name in Contact")
    val(address_type + "_contact_email_rw", "Specify Email address in Address or in Contact (check 'Is Primary')")
    val(address_type + "_contact_phone", "Specify Phone in Address or Contact (check 'Is Primary Phone')")

    return fields

@frappe.whitelist()
def make_shipment_from_dn(source_name, target_doc=None):
    """ To be called from open_mapped_doc. """

    def postprocess(source, target):
        args = frappe.flags.args
        settings = _get_settings()

        # PICKUP
        target.pickup_from_type = "Company"
        target.pickup_contact_person = settings.shipping_contact
        target.update(fill_address_data(
            "pickup", 
            target.pickup_address_name, 
            company=target.pickup_company,
            user=target.pickup_contact_person,
        ))

        # DELIVERY
        target.delivery_to_type = "Customer"
        if source.shipping_address_name:
            target.delivery_address_name = source.shipping_address_name
        elif source.customer_address:
            # Default to billing address
            target.delivery_address_name = source.customer_address

        target.update(fill_address_data(
            "delivery", 
            target.delivery_address_name, 
            customer=target.delivery_customer,
            contact=target.delivery_contact_name,
        ))
        
        # BILL
        target.bill_to_type = "Customer"

        # field_map doesn't allow populating two target fields from same source.
        target.bill_customer = target.delivery_customer
        target.bill_contact_name = target.delivery_contact_name

        target.update(fill_address_data(
            "bill", 
            target.bill_address_name, 
            customer=target.bill_customer,
            contact=target.bill_contact_name,
        ))

        # TIMES
        if args and args.pickup_date:
            target.pickup_date = args.pickup_date
        target.pickup_from = settings.pickup_from
        if args and args.pickup_from:
            target.pickup_from = args.pickup_from
        target.pickup_to = settings.pickup_to

        # FINANCIALS 
        for row in target.items:
            row.currency = source.currency

        shipping = next((t.tax_amount for t in source.taxes if t.account_head == settings.shipping_income_account), 0)
        target.shipment_amount = shipping
        set_totals(target)

    doclist = get_mapped_doc("Delivery Note", source_name, {
        "Delivery Note": {
            "doctype": "Shipment",
            "field_map": {
                "grand_total": "declared_value",
                "currency": "value_currency",
                "company": "pickup_company",
                "company_address": "pickup_address_name",
                "company_address_display": "pickup_address",
                "customer": "delivery_customer",
                "contact_person": "delivery_contact_name",
                "contact_email": "delivery_contact_email",

                "customer_address": "bill_address_name",
                "posting_date": "pickup_date",
                "po_no": "po_no",
            },
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Delivery Note Item": {
            "doctype": "Shipment Item",
            "field_map": {
                "name": "dn_detail",
            }
        }
    }, target_doc, postprocess)

    return doclist

@frappe.whitelist()
def make_return_shipment_from_dn(source_name, target_doc=None):
    """ To be called from open_mapped_doc. """

    def postprocess(source, target):
        settings = _get_settings()

        # PICKUP
        target.pickup_from_type = "Customer"
        target.update(fill_address_data(
            "pickup", 
            target.pickup_address_name, 
            customer=target.pickup_customer,
            contact=target.pickup_contact_name,
        ))

        # DELIVERY
        target.delivery_to_type = "Company"
        target.delivery_user = settings.shipping_contact

        target.update(fill_address_data(
            "delivery", 
            target.delivery_address_name, 
            company=target.delivery_company,
            user=target.delivery_user,
        ))
        
        # BILL
        # field_map doesn't allow populating two target fields from same source.
        target.bill_to_type = "Company"
        target.bill_company = target.delivery_company
        target.bill_address_name = target.delivery_address_name
        target.bill_contact_name = target.delivery_contact_name

        target.update(fill_address_data(
            "bill", 
            target.bill_address_name, 
            company=target.bill_company,
            user=target.delivery_user,
        ))

        # TIMES: best to specify, or they default to currenty time
        # if args and args.pickup_date:
        #     target.pickup_date = args.pickup_date
        target.pickup_from = settings.pickup_from  # Time is set to "now" somehow.
        target.pickup_to = settings.pickup_to

        # FINANCIALS  ETC.
        target.is_return = True
        target.reason_for_export = 'Return'
        for row in target.items:
            row.currency = source.currency

        # Free return shipping
        target.shipment_amount = 0
        set_totals(target)
        set_missing_values(target)

    doclist = get_mapped_doc("Delivery Note", source_name, {
        "Delivery Note": {
            "doctype": "Shipment",
            "field_map": {
                "currency": "value_currency",

                "company": "delivery_company",
                "company_address": "delivery_address_name",

                "customer": "pickup_customer",
                "contact_person": "pickup_contact_name",
                "shipping_address_name": "pickup_address_name",

                "posting_date": "pickup_date",
                "po_no": "po_no",
            },
            "field_no_map": ['shipping_label'],
            # "validation": {
            #     "docstatus": ["=", 1]
            # }
        },
        "Delivery Note Item": {
            "doctype": "Shipment Item",
            "field_map": {
                "name": "dn_detail",
            }
        }
    }, target_doc, postprocess)

    return doclist


@frappe.whitelist()
def finalize_dn(shipment_docname):
    """ Copy AWB number and other relevant information """

    shipment = frappe.get_doc("Shipment", shipment_docname)

    dn_docname = next((i.delivery_note for i in shipment.items if i.delivery_note), None)
    if dn_docname is None:
        raise Exception("No DNs referenced in Shipment")
    dn = frappe.get_doc("Delivery Note", dn_docname)

    if shipment.is_return:
        dn.db_set('return_tracking_no', shipment.awb_number)
        dn.db_set('return_shipping_label', shipment.shipping_label)
    else:
        dn.db_set('tracking_no', shipment.awb_number)
        dn.db_set('pickup_confirmation_number', shipment.pickup_confirmation_number)
        dn.db_set('carrier', shipment.carrier)
        dn.db_set('shipping_label', shipment.shipping_label)
        dn.db_set('packing_stage', 'Shipped')
    

    return dn


@frappe.whitelist()
def ship_from_dn(dn_docname, pickup_date, pickup_from, task_id=None):
    """ Create Shipment doc, request DHL pickup, copy shipping data to DN """
    try:
        return _ship_from_dn(dn_docname, pickup_date, pickup_from, task_id)
    except Exception as e:
        set_status({
            "progress": 100,
            "message": _("Error"),
        }, task_id, STATUS_DONE)

        raise e


def _ship_from_dn(dn_docname, pickup_date, pickup_from, task_id=None):
    """ Create Shipment doc, request DHL pickup, copy shipping data to DN """

    frappe.flags.args = frappe._dict({
        "pickup_date": pickup_date,
        "pickup_from": pickup_from,
    })

    shipment_doc = make_shipment_from_dn(dn_docname)
    shipment_doc.submit() # Will not commit in case of error.

    _create_shipment(shipment_doc.name, pickup=True, task_id=task_id)
    dn = finalize_dn(shipment_doc.name)

    return dn


@frappe.whitelist()
def get_return_label_from_dn(dn_docname, task_id=None):
    """ Create Shipment doc, request shipping label, copy data back to DN """
    try:
        return _get_return_label_from_dn(dn_docname, task_id)
    except Exception as e:
        set_status({
            "progress": 100,
            "message": _("Error"),
        }, task_id, STATUS_DONE)

        raise e


def _get_return_label_from_dn(dn_docname, task_id=None):
    shipment_doc = make_return_shipment_from_dn(dn_docname)
    shipment_doc.submit() # Will not commit in case of error.

    _create_shipment(shipment_doc.name, pickup=False, task_id=task_id)
    dn = finalize_dn(shipment_doc.name)
    return dn


@frappe.whitelist()
def validate_sales_order(name):
    """ Check deliverability of a sales order.

    Return nothing if valid, {error: '', message: ''} otherwise.
     
    """

    so_doc = frappe.get_doc("Sales Order", name)
    settings = _get_settings()

    # Check mandatary fields are filled
    try:
        fill_address_data(
                "pickup", 
                so_doc.company_address, 
                company=so_doc.company,
                user=settings.shipping_contact,
                validate=True
            )
    except AddressError as e:
        return {
            "error": "Our own address is not valid",
            "message": e.message,
        }

    try:
        fill_address_data(
                "delivery", 
                so_doc.shipping_address_name, 
                customer=so_doc.customer,
                contact=so_doc.contact_person,
                validate=True
            )
        validate_address(so_doc.shipping_address_name)
    except AddressError as e:
        return {
            "error": "Shipping address is not valid",
            "message": e.message,
        }

    try:
        fill_address_data(
                "bill", 
                so_doc.customer_address, 
                customer=so_doc.customer,
                contact=so_doc.contact_person,
                validate=True
            )
        validate_address(so_doc.customer_address)
    except AddressError as e:
        return {
            "error": "Billing address is not valid",
            "message": e.message,
        }

    return {
        "error": None,
        "message": "",
    }
    


@frappe.whitelist()
def make_return_shipment_from_so(source_name, target_doc=None):
    """ To be called from open_mapped_doc. """

    def postprocess(source, target):
        settings = _get_settings()

        # PICKUP
        target.pickup_from_type = "Customer"
        target.update(fill_address_data(
            "pickup", 
            target.pickup_address_name, 
            customer=target.pickup_customer,
            contact=target.pickup_contact_name,
        ))

        # DELIVERY
        target.delivery_to_type = "Company"
        target.delivery_user = settings.shipping_contact

        target.update(fill_address_data(
            "delivery", 
            target.delivery_address_name, 
            company=target.delivery_company,
            user=target.delivery_user,
        ))

        # BILL
        # field_map doesn't allow populating two target fields from same source.
        target.bill_to_type = "Company"
        target.bill_company = target.delivery_company
        target.bill_address_name = target.delivery_address_name
        target.bill_contact_name = target.delivery_contact_name

        target.update(fill_address_data(
            "bill", 
            target.bill_address_name, 
            company=target.bill_company,
            user=target.delivery_user,
        ))

        # BUILD ITEMS
        so_item_lookup = {i.name: i for i in source.items}
        target.items = [i for i in target.items if so_item_lookup[i.so_detail].price_list_rate]
        for item in target.items:
            item_master = frappe.get_doc("Item", so_item_lookup[item.so_detail].item_code)
            if item_master.return_value:
                item.rate = item_master.return_value
            item.customs_tariff_number = item_master.customs_tariff_number
            item.country_of_origin = item_master.country_of_origin

        # TIMES: best to specify, or they default to currenty time
        # if args and args.pickup_date:
        target.pickup_date = datetime.date.today()  # Doesn't matter at this point.
        target.pickup_from = settings.pickup_from  # Time is set to "now" somehow.
        target.pickup_to = settings.pickup_to

        # FINANCIALS  ETC.
        target.is_return = True
        target.reason_for_export = 'Return'

        # Free return shipping
        target.shipment_amount = 0
        set_totals(target)
        set_missing_values(target)


    doclist = get_mapped_doc("Sales Order", source_name, {
        "Sales Order": {
            "doctype": "Shipment",
            "field_map": {
                "currency": "value_currency",

                "company": "delivery_company",
                "company_address": "delivery_address_name",

                "customer": "pickup_customer",
                "contact_person": "pickup_contact_name",
                "shipping_address_name": "pickup_address_name",

                "posting_date": "pickup_date",
                "po_no": "po_no",
            },
        },
        "Sales Order Item": {
            "doctype": "Shipment Item",
            "field_map": {
                "name": "so_detail",
            }
        }
    }, target_doc, postprocess)

    return doclist

@frappe.whitelist()
def copy_to_rr(shipment_docname):
    """ Copy AWB number and other relevant information """

    shipment = frappe.get_doc("Shipment", shipment_docname)

    rr_docname = next((i.refill_request for i in shipment.items if i.refill_request), None)
    if rr_docname is None:
        raise Exception("No RRs referenced in Shipment")

    rr = frappe.get_doc("Refill Request", rr_docname)
    rr.db_set('shipping_label', shipment.shipping_label);
    rr.db_set('shipment', shipment_docname);

    return rr