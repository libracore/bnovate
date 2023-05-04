# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class StorageLocation(Document):
	pass

@frappe.whitelist(allow_guest=True)
def find_serial_no(serial_no, throw=True, key=None):
	""" Return storage location of a serial number.

	If key is provided skip authentication. Accept the lookup if secret key corresponds to the 
	storage location.
	"""

	if not key:
		frappe.has_permission("Storage Location", "read", throw=True)

	sql = """
	SELECT
		loc.name AS location,
		loc.title AS title,
		loc.`key` AS secret_key,
		slot.label AS slot,
		slot.name AS slot_docname
	FROM `tabStorage Location` loc
	JOIN `tabStorage Slot` slot ON slot.parent = loc.name
	WHERE slot.serial_no = "{serial_no}"
	""".format(serial_no=serial_no.strip())
	result = frappe.db.sql(sql, as_dict=True)
	if result:
		if key and result[0].secret_key != key:
			frappe.throw("Key does not match.")

		return result[0]

	if throw:
		frappe.throw("Serial number not found: {}".format(serial_no))
	return None
	

@frappe.whitelist(allow_guest=True)
def store_serial_no(location_name, serial_no, key=None):
	""" Find an empty slot, stores SN in it, return slot name """
	if not key:
		frappe.has_permission("Storage Location", "write", throw=True)

	serial_no = serial_no.strip()

	# Check that serial_no is not currently stored:
	location = find_serial_no(serial_no, throw=False, key=key)
	if location is not None:
		frappe.throw("Serial No {} is already stored in {}".format(serial_no, location.title))

	location = frappe.get_doc("Storage Location", location_name)
	if key and location.key != key:
		frappe.throw("Key does not match.")

	for slot in location.slots:
		if slot.serial_no is None:
			slot.db_set("serial_no", serial_no)
			break
	
	return find_serial_no(serial_no)


@frappe.whitelist(allow_guest=True)
def remove_serial_no(serial_no, key=None):
	""" Remove serial number from storage slot """

	if not key:
		frappe.has_permission("Storage Location", "write", throw=True)

	location = find_serial_no(serial_no, key=key)

	if key and location.secret_key != key:
		frappe.throw("Key does not match.")

	slot = frappe.get_doc("Storage Slot", location.slot_docname)
	slot.db_set("serial_no", None)

	return location

