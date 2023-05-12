# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from bnovate.bnovate.utils.iot_apis import rms_get_id, rms_get_device

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