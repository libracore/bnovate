# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from bnovate.bnovate.utils.iot_apis import (rms_get_id, rms_get_device, rms_initialize_device, 
                                            _rms_start_session, rms_get_access_configs)
from bnovate.bnovate.utils.realtime import set_status, STATUS_DONE
from bnovate.bnovate.utils import iot_apis
from bnovate.bnovate.doctype.audit_log import audit_log

class ConnectivityPackage(Document):
    pass


@frappe.whitelist()
def set_info_from_rms(docname):
    """ Fill device info from RMS. """

    cp = frappe.get_doc("Connectivity Package", docname)

    if not cp.teltonika_serial:
        frappe.throw("Serial number not set for connectivity package {}".format(docname))
        return

    rms_id = rms_get_id(cp.teltonika_serial)

    cp.db_set("rms_id", rms_id)

    device = frappe._dict(rms_get_device(rms_id))

    cp.db_set("device_name", device.name)
    cp.db_set("imei", device.imei)
    cp.db_set("mac_address", device.mac)
    cp.db_set("iccid", device.iccid[:19])

    return cp


@frappe.whitelist()
def auto_configure_device(device_id, new_device_name, docname, task_id=None):
    """ Scan ports, add available remotes, refresh RMS info """

    device_id, teltonika_serial = frappe.get_value("Connectivity Package", docname, ['rms_id', 'teltonika_serial'])

    audit_log.log(
        action="Gateway Autoconfiguration Request (backend)",
        data={
            'teltonika_serial': teltonika_serial,
            'device_name': new_device_name,
        },
        connectivity_package=docname,
    )

    raise Exception("Oh noes")

    set_status({
        "progress": 10,
        "message": "Initializing..."
    }, task_id)
    
    rms_initialize_device(device_id, new_device_name)

    set_status({
        "progress": 50,
        "message": "Fetching Gateway Info..."
    }, task_id)

    set_info_from_rms(docname)

    set_status({
        "progress": 80,
        "message": "Fetching Instrument Info..."
    }, task_id)

    sn = get_instrument_sn(docname)

    audit_log.log(
        action="Gateway Autoconfiguration Success (backend)",
        data={
            'teltonika_serial': teltonika_serial,
            'device_name': new_device_name,
        },
        serial_no=sn,
        connectivity_package=docname,
    )

    set_status({
        "progress": 100,
        "message": "Done"
    }, task_id, STATUS_DONE)


@frappe.whitelist()
def get_instrument_sn(docname):
    """ Attempt to read SN from connected instrument, set instrument_serial_no if successful """
    cp = frappe.get_doc("Connectivity Package", docname)
    status = get_instrument_status(docname)
    if status and 'serialNumber' in status:
        cp.db_set("instrument_serial_no", status['serialNumber'])
        return status['serialNumber']


@frappe.whitelist()
def get_instrument_status(docname, task_id=None):
    return _get_instrument_status(docname, task_id)


def _get_instrument_status(docname, auth=True, task_id=None):
    """ Return /api/status of the actual instrument connected to the matching BactoLink.
     
    Skip authentication if you have already authenticated the request, for example from portal.
    task_id: for realtime updates
    """

    rms_id, instrument_serial_no = frappe.get_value("Connectivity Package", docname, ['rms_id', 'instrument_serial_no'])

    audit_log.log(
        action="Get Instrument Status", 
        data={'rms_device_id': rms_id},
        protocol="HTTPS",
        serial_no=instrument_serial_no,
        connectivity_package=docname,
    )

    return iot_apis.get_instrument_status(rms_id, auth=auth, task_id=task_id)


@frappe.whitelist()
def start_session(docname, config_id, task_id=None):
    return _start_session(docname, config_id, task_id=task_id)

def _start_session(docname, config_id, auth=True, task_id=None):
    """ Start remote connection, return URL. 
    
    Adds audit logging. Skip auth only if checked before call.
    """
    rms_id, instrument_serial_no = frappe.get_value("Connectivity Package", docname, ['rms_id', 'instrument_serial_no'])
    access_configs = rms_get_access_configs(rms_id, auth=auth)
    config = next((c for c in access_configs if str(c['id']) == str(config_id)), None) 
    
    audit_log.log(
        action="Start Remote Session", 
        data={
            'rms_device_id': rms_id, 
            'connection_name': config['name'] if config else 'Unknown',
        },
        protocol=config['protocol'].upper() if config else 'Unknown',
        serial_no=instrument_serial_no,
        connectivity_package=docname,
    )

    return _rms_start_session(config_id, rms_id, auth=auth, task_id=task_id)
