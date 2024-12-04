from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'service_report',
		'transactions': [
			{
				'label': _('Sales'),
				'items': ['Sales Order']
			},
		]
	}