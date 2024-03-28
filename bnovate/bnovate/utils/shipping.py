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
