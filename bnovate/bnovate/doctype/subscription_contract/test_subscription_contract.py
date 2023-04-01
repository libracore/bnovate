# -*- coding: utf-8 -*-
# Copyright (c) 2023, bNovate, libracore and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

test_records = frappe.get_test_records("Sales Order")

def create_fixtures():
	if frappe.flags.test_subs_created:
		return

	for record in test_records:
		frappe.get_doc(record).insert()
	doc = frappe.get_doc({
		'doctype': 'Subscription Contract',
		'start_date': '2023-02-20',
		'customer': '_Test Customer',
	}).insert()

	frappe.flags.test_subs_created = True

class TestSubscriptionContract(unittest.TestCase):
	def setUp(self):
		create_fixtures()


# test_dependencies = ["Sales Order"]