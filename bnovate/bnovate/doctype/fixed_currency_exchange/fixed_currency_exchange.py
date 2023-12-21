# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from erpnext.setup.doctype.currency_exchange.currency_exchange import CurrencyExchange

class FixedCurrencyExchange(CurrencyExchange):
	""" Inherit standard currency exchange """
	pass
