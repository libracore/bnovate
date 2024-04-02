# -*- coding: utf-8 -*-
# Copyright (c) bNovate (Douglas Watson)
# For license information, please see license.txt
#
# Wrappers for DHL APIs
# -------------------------
#
#######################################################################

import frappe

from json import JSONDecodeError

from frappe import _
from requests import request

READ, WRITE = "read", "write"

class DHLException(Exception):
    pass

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
    """ Make request to DHL API """
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
    ).json()

    return resp


#######################
# WRAPPERS
#######################

@frappe.whitelist()
def get_price(shipment_docname):
    settings = _get_settings()
    doc = frappe.get_doc("Shipment", shipment_docname)

    body = {
        "productCode": "N",
        "localProductCode": "N",
        "customerDetails": {
            "shipperDetails": {
                "countryCode": "CH",
                "cityName": "Lausanne",
                "postalCode": "1015"
            },
            "receiverDetails": {
        "countryCode": "CH",
        "cityName": "Zurich",
                "postalCode": "5000"
            }
        },
        "accounts": [{
            "typeCode": "shipper",
            "number": settings.dhl_export_account,
        }],
        "packages": [{
            "weight": 5,
            "dimensions": {
                "length": 15,
                "width": 10,
                "height": 5
            }
        }],
        "plannedShippingDateAndTime": "2024-03-08T17:00:31GMT+01:00",
        "isCustomsDeclarable": False,
        "unitOfMeasurement": "metric"
    }

    resp = dhl_request("/rates", 'POST', body=body, settings=settings)

    print("\n\n\n--------------------------------------------\n\n\n")
    print("\n\n\n--------------------------------------------\n\n\n")
    print(resp)
    print("\n\n\n--------------------------------------------\n\n\n")
    
    return resp