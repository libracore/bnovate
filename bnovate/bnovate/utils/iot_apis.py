# -*- coding: utf-8 -*-
# Copyright (c) bNovate (Douglas Watson)
# For license information, please see license.txt

import json
import frappe
import requests

@frappe.whitelist()
def simbase_get_cards():
    settings = frappe.get_single("bNovate Settings")
    return requests.request(
        "GET", 
        "https://api.simbase.com/simcards", 
        headers={"x-api-key": settings.simbase_api_key}
    ).json()

@frappe.whitelist()
def rms_get_devices():
    settings = frappe.get_single("bNovate Settings")
    # return mock
    return requests.request(
        "GET", 
        "https://rms.teltonika-networks.com/api/devices", 
        headers={"Authorization": "Bearer {}".format(settings.rms_api_token)}
    ).json()



