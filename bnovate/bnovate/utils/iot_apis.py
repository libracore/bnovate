# -*- coding: utf-8 -*-
# Copyright (c) bNovate (Douglas Watson)
# For license information, please see license.txt
#
# Wrappers for various APIs.
# -------------------------
#
#######################################################################

import time
import frappe
import concurrent.futures

from json import JSONDecodeError
from requests import request
from requests.auth import HTTPBasicAuth

READ, WRITE = "read", "write"

class ApiException(Exception):
    pass

class NoEndDevicesFound(ApiException):
    """ No end devices were found during port scan. """
    pass

class ChannelNotFound(ApiException):
    """ Raised when a status channel isn't found - may be too early, try again """

#######################
# HELPERS
#######################

def _auth(ptype=READ):
    return frappe.has_permission("Connectivity Package", ptype, throw=True)

def _get_settings():
    return frappe.get_single("bNovate Settings")

#######################
# BASE API CONNECTIONS
#######################

def _rms_get_status(channel, auth=True):
    """ Return status updates on given channel, 
    
    Use in situations where authentication should be checked separately  
    """
    if auth:
        _auth(READ)
    settings = _get_settings()

    resp = request(
        "GET", 
        "https://rms.teltonika-networks.com/status/channel/" + channel,
        headers={"Authorization": "Bearer {}".format(settings.rms_api_token)}
    )

    if resp.status_code != 200:

        detail = resp.text
        try:
            detail = resp.json()
            if detail['code'] == 'CHANNEL_NOT_FOUND':
                raise ChannelNotFound("Channel doesn't exist or expired:", channel)
        except JSONDecodeError:
            pass
        raise ApiException("Error fetching RMS Status: " + str(detail))
    return resp.json()['data']

@frappe.whitelist()
def rms_get_status(channel):
    """ Return status updates on given channel, can be called from Desk  """
    # Response and error handling are slightly different from regular API
    return _rms_get_status(channel, auth=True)

def rms_monitor_status(channel, device_id, attempt=0, auth=True):
    """ Monitor status channel until completion or error """
    if attempt >= 30:
        raise ApiException("Timeout requesting status update from channel{}".format(channel))
    try:
        resp = _rms_get_status(channel, auth)
    except ChannelNotFound:
        time.sleep(1)
        return rms_monitor_status(channel, device_id, attempt + 1, auth)

    if device_id not in resp:
        raise ApiException("No status update for device {} in channel {}".format(device_id, channel))

    updates = resp[device_id]

    if updates and updates[-1]['status'] in ("error", "completed"):
        if updates[-1]['status'] == "error":
            raise ApiException(updates[-1]['value'])
        return updates[-1]

    time.sleep(0.5)
    return rms_monitor_status(channel, device_id, attempt + 1, auth)


def rms_request(path, method='GET', params=None, body=None, settings=None, auth=True):
    """ Skip auth when running parallel requests, just make sure to check at least once! """
    if auth:
        _auth(READ if method == 'GET' else WRITE)
    if settings is None:
        settings = _get_settings()
    resp = request(
        method, 
        "https://rms.teltonika-networks.com" + path,
        params=params,
        json=body,
        headers={"Authorization": "Bearer {}".format(settings.rms_api_token)}
    ).json()
    if not resp['success']:
        raise ApiException("Error fetching from RMS API: " + str(resp['errors']))
    if 'data' not in resp and 'meta' in resp:
        return resp['meta']
    elif 'data' in resp:
        return resp['data']


##################################
# WRAPPERS
##################################

@frappe.whitelist()
def rms_get_device(device_id):
    return _rms_get_device(device_id)

def _rms_get_device(device_id, auth=True):
    """ Return info from single device """
    return rms_request("/api/devices/{id}".format(id=device_id), auth=auth)


def rms_set_device(device_id, payload, auth=True):
    """ Set device data """
    return rms_request("/api/devices/{}".format(device_id),
    "PUT",
    body=payload,
    auth=auth)


def rms_get_devices(settings=None):
    """ Return list of all devices connected to RMS """
    return rms_request("/api/devices", settings=settings)


@frappe.whitelist()
def rms_get_id(serial):
    matches = [d for d in rms_get_devices() if d['serial'] == serial]
    if matches:
        return matches[0]['id']
    return None

def rms_port_scan(device_id, auth=True):
    """ Return available IPs and ports, i.e. instruments connected to device 

    Example return value:

    [{
            "ip": "192.168.2.148",
            "mac": "...",
            "port": [ 22, 80, 443, 5900 ],
            "vendor": "..."
    }],

    """
    meta = rms_request(
        "/api/devices/{}/port-scan".format(device_id),
        params={"type": "ethernet"},
        auth=auth
    )
    ports_info = rms_monitor_status(meta['channel'], device_id, auth=auth)
    if not 'ports' in ports_info \
            or not ports_info['ports'] \
            or not 'devices' in ports_info['ports'][0] \
            or not ports_info['ports'][0]['devices']:
        raise NoEndDevicesFound("No end devices found")
    
    return ports_info['ports'][0]['devices'][0]


def rms_create_access(device_id, payload, auth=True):
    """ Create remote access configurations. See API reference for payload format. """
    meta = rms_request(
        "/api/devices/remote-access",
        "POST",
        body=payload,
        auth=auth
    )
    return rms_monitor_status(meta['channel'], device_id, auth=auth)


def rms_delete_access(device_id, config_ids, auth=True):
    """ Delete access configurations based on IDs.

    config_ids: array of int
    """
    # Mistake in RMS API: it doesn't loop IDs. Need to do it ourselves:
    for id in config_ids:
        meta = rms_request(
            "/api/devices/remote-access",
            "DELETE",
            body={'id': [id]},
            auth=auth
        )
        rms_monitor_status(meta['channel'], device_id, auth=auth)



def rms_initialize_device(device_id, device_name, auth=True):
    """ Create remote configurations for a device. """

    # 0) Rename device and clear up existing access configs
    # 1) Port scan
    # 2) Create HTTPS and VNC remotes for first available end-device

    # Rename
    rms_set_device(device_id, {
        "name": device_name,
    }, auth)

    # Delete existing remote configs (if no end devices are available, we shouldn't display outdated configs)
    configs = rms_get_access_configs(device_id, auth=auth)
    if  configs:
        rms_delete_access(device_id, 
            [c['id'] for c in configs if c['protocol'] in ("https", "vnc")],
            auth=auth)
        
    # Port Scan
    try:
        end_devices = rms_port_scan(device_id, auth)
    except NoEndDevicesFound:
        frappe.throw("No instruments connected to this Link.")

    ip, ports = end_devices['ip'], end_devices['port']
    data = []
    if 443 in ports:
        data.append({
            "device_id": device_id,
            "name": "{} Web Interface".format(device_name),
            "destination_ip": ip,
            "destination_port": 443,
            "protocol": "https",
            "credentials_required": False,
        })

    if 5900 in ports:
        data.append({
            "device_id": device_id,
            "name": "{} Remote Desktop".format(device_name),
            "destination_ip": ip,
            "destination_port": 5900,
            "protocol": "vnc",
            "credentials_required": False,
        })

    # Set new configs, if available
    if data:
        # raise ApiException("Neither HTTPS or VNC available on this device")
        return rms_create_access(device_id, {"data": data}, auth)
    
    # False inform that neithe HTTPS nor VNC are available.
    return False


def rms_get_access_configs(device_id=None, settings=None, auth=True):
    """ Return list of access configs based on RMS ID (not SN). """
    params = None
    if device_id:
        params = {'device_id': device_id}
    configs = rms_request(
        "/api/devices/remote-access", 
        params=params,
        settings=settings,
        auth=auth,
    )
    return [c for c in configs if c['protocol']]

def rms_get_access_sessions_for_config(config, settings=None, auth=True):
    """ Return active access session urls for a given access config """
    sessions = rms_request(
        "/api/devices/connect/{config_id}/sessions".format(config_id=config['id']),
        settings=settings,
        auth=auth,
    )

    active = [s for s in sessions if s['end_time'] > time.time()]
    active.sort(key=lambda el: el['end_time'], reverse=True)
    return dict(sessions=active, **config)

@frappe.whitelist()
def rms_get_access_sessions(device_id=None):
    """ Return list of access config dicts, each with its list of active sessions """
    _auth(WRITE)  # require write permissions since this returns active session links
    settings = _get_settings()
    configs = rms_get_access_configs(device_id, settings=settings)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [ executor.submit(rms_get_access_sessions_for_config, c, settings=settings, auth=False) for c in configs ]
        responses = [ future.result() for future in concurrent.futures.as_completed(futures) ]

    # Alphabetical sort by protocol, so that they always appear in the same order.
    responses.sort(key=lambda el: el['protocol'])
    return responses

def _rms_start_session(config_id, duration=30*60, auth=True):
    """ Opens a new session for an existing remote configuration. 

    Auth can be checked separately for portal users.
    """
    resp = rms_request(
        "/api/devices/connect/{config_id}".format(config_id=config_id),
        "POST",
        body={"duration": duration},
        auth=auth
    )
    return resp['channel']

@frappe.whitelist()
def rms_start_session(config_id, duration=30*60):
    """ Opens a new session for an existing remote configuration. 

    Auth handled for Desk users
    """
    return _rms_start_session(config_id, duration)




def combase_get_usage(iccid, settings=None, auth=True):
    """ Return data usage of SIM card in MB, or None.


    Skip permission check if these are called concurrently. Just make sure to 
    check at least once calling _auth()!
    
    """
    if auth:
        _auth()
    if settings is None:
        settings = _get_settings()

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

    settings = _get_settings()
    devices = rms_get_devices(settings=settings)

    # To avoid modifying memory in the parallel fetches, build dict of iccid: data_usage:
    iccids = [ device['iccid'][:19] for device in devices if 'iccid' in device ]


    # Get data usage for each SIM iccid:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [ executor.submit(combase_get_usage, iccid, settings, auth=False) for iccid in iccids ]
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

