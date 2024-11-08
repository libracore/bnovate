# Copyright (c) 2024, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    # add head column
    columns = [
        {'fieldname': 'account_group', 'label': 'Account Group', 'fieldtype': 'Data', 'width': 150}
    ]
    # add column per company
    companies = frappe.get_all("Company", fields=['name', 'abbr'])
    for c in companies:
        columns.append({
            'fieldname': 'value_{0}'.format(c['abbr']),
            'label': c['abbr'],
            'fieldtype': 'Currency',
            'width': 80
        })
        
    return columns
    
def get_data(filters=None):
    data = [{'account_group': 'TEST'}]
    
    return data
    
