# -*- coding: utf-8 -*-
# Copyright (c) 2023, bNovate, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json

import frappe
from frappe.model.document import Document

class AuditLog(Document):
	pass


def log(action, data, protocol=None, serial_no=None, connectivity_package=None, commit=True):
	""" Add audit log entry 
	"""

	new_log = frappe.get_doc({
		'doctype': 'Audit Log',
		'docstatus': 1,
		'action': action,
		'data': json.dumps(data),
		'protocol': protocol,
		'serial_no': serial_no,
		'connectivity_package': connectivity_package,
	})

	new_log.insert(ignore_permissions=True)

	if commit:
		frappe.db.commit()
		
	return new_log
