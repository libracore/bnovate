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
    data = []
    
    account_groups = frappe.get_all(
        "IC Account Group", 
        filters=[['reporting_type', 'IN', 'Asset, Liability, Equity']], 
        fields=['name'],
        order_by='title ASC'
    )
    
    for ag in account_groups:
        _data = {
            'account_group': ag['name']
        }
        _data.update(get_balance_for_account_group(account_group=ag['name'], to_date=filters.get('to_date')))
        data.append( _data )
        
    return data
    

def get_balance_for_account_group(account_group, to_date):
    group_doc = frappe.get_doc("IC Account Group", account_group)
    group_balances = {}
    for account in group_doc.accounts:
        if account.abbr not in group_balances:
            group_balances[account.abbr] = 0
        group_balances[account.abbr] += get_balance(account.account, to_date)
    
    return group_balances
    
def get_balance(account, to_date):
    balance = frappe.db.sql("""
        SELECT IFNULL(SUM(`debit`), 0) - IFNULL(SUM(`credit`), 0) AS `balance`
        FROM `tabGL Entry`
        WHERE
            `account` = "{account}"
            AND `posting_date` <= "{to_date}"
        ;""".format(account=account, to_date=to_date), as_dict=True)
    if len(balance) > 0:
        return balance[0]['balance']
    else:
        return 0
        
