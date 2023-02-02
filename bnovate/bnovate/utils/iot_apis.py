# -*- coding: utf-8 -*-
# Copyright (c) bNovate (Douglas Watson)
# For license information, please see license.txt

import json
import frappe
import requests

def rms_request(path, method="GET"):
    settings = frappe.get_single("bNovate Settings")
    return requests.request(
        method, 
        "https://rms.teltonika-networks.com/api" + path,
        headers={"Authorization": "Bearer {}".format(settings.rms_api_token)}
    ).json()

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
    return rms_request("/devices")

@frappe.whitelist()
def rms_get_sim_iccid(device_id):
    # Fetch latest date and time for device, then get SIM card value
    dates = rms_request("/devices/{device_id}/information-history/datetimes".format(device_id=device_id))
    if not dates['success'] or not dates['data']:
        # TODO: raise error
        return
    
    datetime = dates['data'][0]['date'] + " " + dates['data'][0]['times'][0]
    print("Latest datetime available: ", datetime)
    info = rms_request("/devices/{device_id}/information-history?datetime={datetime}".format(device_id=device_id, datetime=datetime))

    if not info['success'] or not info['data']:
        # TODO: raise error
        return

    return info['data'][0]['iccid']
