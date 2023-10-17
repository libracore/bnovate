# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
        {'fieldname': 'contact_docname', 'fieldtype': 'Link', 'label': _('Contact'), 'options': 'Contact', 'width': 100},
        {'fieldname': 'first_name', 'fieldtype': 'Data', 'label': _('First Name'), 'width': 100},
        {'fieldname': 'last_name', 'fieldtype': 'Data', 'label': _('Last Name'), 'width': 100},
        {'fieldname': 'user', 'fieldtype': 'Link', 'label': _('Username'), 'options': 'User', 'width': 100},
        {'fieldname': 'customer_docname', 'fieldtype': 'Link', 'label': _('Customer'), 'options': 'Customer', 'width': 100},
        {'fieldname': 'customer_name', 'fieldtype': 'Data', 'label': _('Customer Name'), 'width': 100},
        {'fieldname': 'enable_cartridge_portal', 'fieldtype': 'Check', 'label': _('Has Cartridge Portal'), 'width': 100},
        {'fieldname': 'primary_customer', 'fieldtype': 'Check', 'label': _('Is Primary Customer'), 'width': 100},
	]

def get_data(filters):
	if not filters.customer:
		filters.customer = "%"
	if not filters.name:
		filters.name = "%"

	sql_query = """
	SELECT
		c.name AS contact_docname,
		c.first_name,
		c.last_name,
		c.user,
		dl.name,
		dl.idx,
		cu.name AS customer_docname,
		cu.customer_name,
		cu.enable_cartridge_portal,
		(dl.idx = 1) AS primary_customer
	FROM `tabContact` c
	JOIN `tabUser` u on u.name = c.user
	JOIN `tabDynamic Link` dl ON dl.parenttype = "Contact" AND dl.link_doctype = "Customer" AND dl.parent = c.name
	JOIN `tabCustomer` cu ON cu.name = dl.link_name
	WHERE cu.name LIKE "{customer_docname}"
		AND (c.first_name LIKE "%{contact_name}%" OR c.last_name LIKE "%{contact_name}%")
	ORDER BY user, idx
	""".format(customer_docname=filters.customer, contact_name=filters.name)
	return frappe.db.sql(sql_query, as_dict=True)