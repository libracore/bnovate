# (C) 2023, bNovate
#
# Custom dashboard code for standard doctypes.

from __future__ import unicode_literals
import frappe
from frappe import _

def get_serial_no_dashboard_data(data):
    print("\n\n\n\n--------------------", data)
    return frappe._dict({
        'fieldname': 'serial_no',
        'non_standard_fieldnames': {},
        'transactions': [
            {
                'label': _('Add-ons'),
                'items': ['License Key'],
            }
        ],
    })
