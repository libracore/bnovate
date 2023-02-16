# -*- coding: utf-8 -*-
# Copyright (c) bNovate (Douglas Watson)
# For license information, please see license.txt

from distutils.command.config import config
from http.client import responses
import time
import frappe
import concurrent.futures

from requests import request
from requests.auth import HTTPBasicAuth

def _get_settings():
    return frappe.get_single("bNovate Settings")

@frappe.whitelist()
def rms_request(path, method='GET', params=None, settings=None):
    if settings is None:
        settings = _get_settings();
    return request(
        method, 
        "https://rms.teltonika-networks.com/api" + path,
        params=params,
        headers={"Authorization": "Bearer {}".format(settings.rms_api_token)}
    ).json()

def rms_get_devices(settings=None):
    """ Return list of all devices connected to RMS """
    return rms_request("/devices", settings=    settings)['data']

@frappe.whitelist()
def rms_get_id(serial):
    matches = [ d for d in rms_get_devices() if d['serial'] == serial]
    if matches:
        return matches[0]['id']
    return None

def rms_get_access_configs(device_id=None, settings=None):
    """ Return list of access configs based on RMS ID (not SN). """
    params = None
    if device_id:
        params = {'device_id': device_id}
    configs = rms_request(
        "/devices/remote-access", 
        params=params,
        settings=settings,
    )['data']
    return [c for c in configs if c['protocol']]

def rms_get_access_sessions_for_config(config, settings=None):
    """ Return active access session urls for a given access config """
    sessions = rms_request(
        "/devices/connect/{config_id}/sessions".format(config_id=config['id']),
        settings=settings)['data']

    active = [s for s in sessions if s['end_time'] > time.time()]
    active.sort(key=lambda el: el['end_time'])
    return dict(sessions=active, **config)

@frappe.whitelist()
def rms_get_access_sessions(device_id=None):
    """ Return list of access config dicts, each with its list of active sessions """
    settings = _get_settings()
    configs = rms_get_access_configs(device_id, settings=settings)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [ executor.submit(rms_get_access_sessions_for_config, c, settings=settings) for c in configs ]
        responses = [ future.result() for future in concurrent.futures.as_completed(futures) ]

    return responses


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

