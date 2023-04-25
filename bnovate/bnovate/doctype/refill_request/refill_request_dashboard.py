from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'refill_request',
		'internal_links': {
			'Serial No': ['items', 'serial_no'],
		},
		'transactions': [
			{
				'label': _('Sales'),
				'items': ['Sales Order']
			},
			{
				'label': _('Cartridges'),
				'items': ['Serial No']
			},
		]
	}