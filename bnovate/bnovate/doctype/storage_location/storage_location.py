# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class StorageLocation(Document):
	pass

@frappe.whitelist()
def find_serial_no(serial_no, throw=True):
	""" Return storage location of a serial number """

	frappe.has_permission("Storage Location", "read", throw=True)

	sql = """
	SELECT
		loc.name AS location,
		loc.title AS title,
		slot.label AS slot,
		slot.name AS slot_docname
	FROM `tabStorage Location` loc
	JOIN `tabStorage Slot` slot ON slot.parent = loc.name
	WHERE slot.serial_no = "{serial_no}"
	""".format(serial_no=serial_no)
	result = frappe.db.sql(sql, as_dict=True)
	if result:
		return result[0]

	if throw:
		frappe.throw("Serial number not found: {}".format(serial_no))
	return None
	

@frappe.whitelist()
def remove_serial_no(serial_no):
	""" Remove serial number from storage slot """

	frappe.has_permission("Storage Location", "write", throw=True)

	location = find_serial_no(serial_no)
	doc = frappe.get_doc("Storage Slot", location.slot_docname)
	doc.db_set("serial_no", None)

	return location


@frappe.whitelist()
def store_serial_no(location_name, serial_no):
	""" Find an empty slot, stores SN in it, return slot name """

	frappe.has_permission("Storage Location", "write", throw=True)

	# Check that serial_no is not currently stored:
	location = find_serial_no(serial_no, throw=False)
	if location is not None:
		frappe.throw("Serial No {} is already stored in {}".format(serial_no, location.title))

	location = frappe.get_doc("Storage Location", location_name)
	for slot in location.slots:
		if slot.serial_no is None:
			slot.db_set("serial_no", serial_no)
			break
	
	return find_serial_no(serial_no)
