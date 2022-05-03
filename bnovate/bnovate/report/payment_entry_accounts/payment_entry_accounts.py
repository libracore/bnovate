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
        {'fieldname': 'date', 'fieldtype': 'Date', 'label': _('Date'), 'width': 80},
        {'fieldname': 'payment_entry', 'fieldtype': 'Link', 'label': _('PE'), 'options': 'Payment Entry', 'width': 80},
        {'fieldname': 'invoice', 'fieldtype': 'Link', 'label': _('PINV'), 'options': 'Purchase Invoice', 'width': 100},
        {'fieldname': 'supplier', 'fieldtype': 'Link', 'label': _('Supplier'), 'options': 'Supplier', 'width': 120},
        {'fieldname': 'account', 'fieldtype': 'Link', 'label': _('Account'), 'options': 'Account', 'width': 200},
        {'fieldname': 'amount', 'fieldtype': 'Currency', 'label': _('Amount'), 'width': 100},
    ]
    
    
    
def get_data(filters):

    sql_query = """
SELECT 
  pe.reference_date as "date",
  pe.name as "payment_entry",
  per.reference_name as "invoice",
  pinv.supplier as "supplier",
  sup.supplier_name as "supplier_name",
  pinvi.expense_account as "account",
  pinvi.base_net_amount as "amount" -- Same column as in "Item-wise Purchase Register"
from `tabPayment Entry` as pe
JOIN `tabPayment Entry Reference` per on pe.name = per.parent
JOIN `tabPurchase Invoice` pinv on per.reference_name = pinv.name
JOIN `tabSupplier` sup on pinv.supplier = sup.name
RIGHT JOIN `tabPurchase Invoice Item` pinvi on pinv.name = pinvi.parent
WHERE per.reference_doctype = "Purchase Invoice"
ORDER BY pe.name, pinv.name, pinvi.base_net_amount DESC 
    ;
    """

    data = frappe.db.sql(sql_query, as_dict=True)
    return data
