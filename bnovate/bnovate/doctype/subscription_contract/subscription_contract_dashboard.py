from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'subscription',
		'internal_links': {
			'Quotation': ['items', 'prevdoc_docname'],
			'Serial No': ['assets', 'serial_no'],
			# TODO: Can't link to Connectivity packages, links always point to document name, not a field.
			# Alternatives: monkey patch dashboard code or link to a report.
			# 'Connectivity Package': ['assets', 'serial_no'],
		},
		'transactions': [
			{
				'label': _('Sales'),
				'items': ['Quotation', 'Sales Invoice']
			},
			{
				'label': _('Assets'),
				'items': ['Serial No']
			},
			{
				'label': _('Service'),
				'items': ['Service Report']
			},
		]
	}