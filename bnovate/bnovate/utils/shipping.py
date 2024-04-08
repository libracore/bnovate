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
        "addressLine1": address_line1[:45] if address_line1 else None,
        "addressLine2": address_line2[:45] if address_line2 else None,
        "cityName": city,
        "postalCode": pincode,
        "countryCode": get_country_code(country),
    }
    return frappe._dict({k: v for k, v in address.items() if v})


#######################
# WRAPPERS
#######################

@frappe.whitelist()
def validate_address(name, throw_error=True):
    """ Validate an address for delivery. For now we only look at postal code and country """

    doc = frappe.get_doc("Address", name)
    address = build_address(doc.address_line1, doc.address_line2, doc.city, doc.pincode, doc.country)

    try:
        return _validate_address(address, DELIVERY)
    except AddressError:
        if throw_error:
            frappe.throw("Invalid postal code")
        return False


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
        raise ProductNotFoundError()

    return quote


@frappe.whitelist()
def create_shipment(shipment_docname, task_id=None):
    try:
        _create_shipment(shipment_docname, task_id)
    except Exception as e:
        set_status({
            "progress": 100,
            "message": _("Error"),
        }, task_id, STATUS_DONE)

        raise e
def _create_shipment(shipment_docname, task_id=None):
    """ Create Shipment, receive shipping label and tracking number. 

    Set validate_only to True to check deliverability etc.
    
    """

    set_status({
        "progress": 0,
        "message": _("Initiating request..."),
    }, task_id)

    settings = _get_settings()
    doc = frappe.get_doc("Shipment", shipment_docname)

    if len(doc.shipment_parcel) == 0:
        raise MissingParcelError(_("Please specify types of parcel"))
    if doc.delivery_country != doc.bill_country:
        raise DropShipImpossible(_("Delivery country must be the same as Bill country"))


    product_code = "P"
    local_product_code = "S"
    customs_declarable = True
    value_added_services = [{
        # Paperless trade
        "serviceCode": "WY",
    }]
    if doc.incoterm == "DDP":
        value_added_services += [{
            "serviceCode": "DD",  # Duty paid
        }]

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
    pickup_gmt_offset = _validate_address(pickup_address, PICKUP)
    _validate_address(delivery_address, DELIVERY)
    _validate_address(bill_address, DELIVERY)

    # Commercial invoice data
    invoice_contact = frappe.get_doc("User", settings.shipping_contact)
    invoice_contact.full_name = ' '.join([invoice_contact.first_name, invoice_contact.last_name]).strip()
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
                    "price": i.rate if i.rate > 0 else 1, # TODO find better
                    "description": i.item_name,
                    "weight": {
                        "netValue": i.total_weight or 1.0,
                        "grossValue": i.total_weight or 1.0,
                    },
                    "exportReasonType": get_export_reason_type(doc.reason_for_export),
                    "manufacturerCountry": get_country_code(i.country_of_origin)
                } for i in doc.shipment_delivery_note],
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
    doc.db_set("tracking_url", resp['trackingUrl'])
    if 'cancelPickupUrl' in resp:
        doc.db_set("cancel_pickup_url", resp['cancelPickupUrl'])
    doc.db_set("status", "Booked")
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
            folder="Home", # TODO try Home
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


#######################################
# EXTENSIONS TO SHIPMENT DOCTYPE
#######################################

@frappe.whitelist()
def fill_address_data(address_type, address_name,  company=None, customer=None, supplier=None, contact=None, user=None):
    """ Return address fields for given business / address / contact. 

    Fills as much data as possible from the address.

    Tax info is fetched from the business doctype (company, customer, or supplier).

    If missing:
    - company name is taken from business doctype
    - name, email, phone are taken from the person doctype (contact or user)
    
    """

    if address_type not in ('pickup', 'delivery', 'bill'):
        raise ValueError("address_type must be one of ('pickup', 'delivery', 'bill')")

    if company:
        business_doc = frappe.get_doc("Company", company)
        business_doc.company_name = business_doc.name
    elif customer:
        business_doc = frappe.get_doc("Customer", customer)
        business_doc.company_name = business_doc.customer_name
    elif supplier:
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
        return email_id.split(',')[0]

    return {
        address_type + "_company_name": address_doc.company_name or business_doc.company_name,
        address_type + "_tax_id": business_doc.tax_id,
        address_type + "_eori_number": business_doc.eori_number,
        address_type + "_address_line1": address_doc.address_line1,
        address_type + "_address_line2": address_doc.address_line2,
        address_type + "_pincode": address_doc.pincode,
        address_type + "_city": address_doc.city,
        address_type + "_country": address_doc.country,
        address_type + "_contact_display": address_doc.contact_name or contact_doc.contact_display, 
        address_type + "_contact_email_rw": trim_email(address_doc.email_id or contact_doc.email),
        address_type + "_contact_phone": address_doc.phone or contact_doc.phone,
    }


@frappe.whitelist()
def make_shipment_from_dn(source_name, target_doc=None):
    """ To be called from open_mapped_doc. """

    # Args are passed through flags
    args = frappe.flags.args
    settings = _get_settings()

    def postprocess(source, target):

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
        target.bill_customer = source.customer
        target.bill_contact_name = source.contact_person

        target.update(fill_address_data(
            "bill", 
            target.bill_address_name, 
            customer=target.bill_customer,
            contact=target.bill_contact_name,
        ))
        

        for row in target.shipment_delivery_note:
            row.currency = source.currency
        
        # TIMES
        if args.pickup_date:
            target.pickup_date = args.pickup_date
        target.pickup_date
        target.pickup_from = settings.pickup_from  # Time is set to "now" somehow.
        target.pickup_to = settings.pickup_to

        # SHIPPING DATA
        shipping = next((t.tax_amount for t in source.taxes if t.account_head == settings.shipping_income_account), 0)
        target.shipment_amount = shipping

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