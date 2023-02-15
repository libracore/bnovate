# -*- coding: utf-8 -*-
# Copyright (c) bNovate (Douglas Watson)
# For license information, please see license.txt

from http.client import responses
import json
import frappe
import concurrent.futures

from requests import request
from requests.auth import HTTPBasicAuth

def rms_get_devices(settings=None):
    if settings is None:
        settings = frappe.get_single("bNovate Settings")
    return request(
        'GET', 
        "https://rms.teltonika-networks.com/api/devices",
        headers={"Authorization": "Bearer {}".format(settings.rms_api_token)}
    ).json()['data']

def combase_get_usage(iccid, settings=None):
    """ Return data usage of SIM card in MB, or None """
    if settings is None:
        settings = frappe.get_single("bNovate Settings")

    resp = request(
        "GET", 
        "https://restapi2.jasper.com/rws/api/v1/devices/{iccid}/ctdUsages".format(iccid=iccid), 
        auth=HTTPBasicAuth(settings.combase_api_username, settings.combase_api_key)
    ).json()

    if not 'ctdDataUsage' in resp:
        return None
    return (iccid, resp['ctdDataUsage'] / 1024 / 1024)


@frappe.whitelist()
def get_devices_and_data():
    """ Return list of all devices including combase data usage in MB """
    devices = rms_get_devices()

    settings = frappe.get_single("bNovate Settings")

    # To avoid modifying memory in the parallel fetches, build dict of iccid: data_usage:
    iccids = [ device['iccid'][:19] for device in devices if 'iccid' in device ]


    # Get data usage for each SIM iccid:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [ executor.submit(combase_get_usage, iccid, settings) for iccid in iccids ]
        responses = [ future.result() for future in concurrent.futures.as_completed(futures) ]
        lookup = { k: v for k, v in responses }

    # And assign to respective devices
    for device in devices:
        device['sim_data_usage_mb'] = None

        if 'iccid' not in device:
            continue

        iccid = device['iccid'][:19]
        if iccid not in lookup:
            return
        device['sim_data_usage_mb'] = lookup[iccid]

    return devices
