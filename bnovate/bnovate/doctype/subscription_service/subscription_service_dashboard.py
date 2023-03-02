from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'subscription',
		'transactions': [
			{
				'label': _('Invoicing'),
				'items': ['Sales Invoice']
			},
			{
				'label': _('Packages'),
				'items': ['Connectivity Package']
			},
		]
	}