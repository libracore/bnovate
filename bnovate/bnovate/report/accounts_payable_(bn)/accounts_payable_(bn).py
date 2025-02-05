# Copyright (c) 2025, bNovate, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe

def execute(filters=None):
    return get_columns(), get_data(filters)

def get_columns():
    return [
        {
            "fieldname": "posting_date",
            "label": "Posting Date",
            "fieldtype": "Date",
            "width": 100
        }, {
            "fieldname": "due_date",
            "label": "Due Date",
            "fieldtype": "Date",
            "width": 100
        }, {
            "fieldname": "payment_terms",
            "label": "Payment Terms (days)",
            "fieldtype": "Int",
            "width": 100
        }, {
            "fieldname": "days_till_due",
            "label": "Days Till Due",
            "fieldtype": "Int",
            "width": 100
        }, {
            "fieldname": "supplier",
            "label": "Supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 120
        }, {
            "fieldname": "supplier_name",
            "label": "Supplier Name",
            "fieldtype": "Data",
            "width": 150
        }, {
            "fieldname": "voucher",
            "label": "Voucher",
            "fieldtype": "Link",
            "options": "Purchase Invoice",
            "width": 120
        }, {
            "fieldname": "document_currency",
            "label": "Document Currency",
            "fieldtype": "Data",
            "width": 100
        }, {
            "fieldname": "grand_total",
            "label": "Grand Total (Doc Currency)",
            "fieldtype": "Currency",
            "options": "document_currency",
            "width": 120
        }, {
            "fieldname": "payables_account",
            "label": "Payables Account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 150
        }, {
            "fieldname": "payables_currency",
            "label": "Payables Currency",
            "fieldtype": "Data",
            "width": 100
        }, {
            "fieldname": "outstanding_amount",
            "label": "Outstanding Amount (Doc. Currency)",
            "fieldtype": "Currency",
            "options": "payables_currency",
            "width": 120
        }, {
            "fieldname": "company",
            "label": "Company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 150
        }
    ]


def get_data(filters):

    # WARNINGS
    # An invoice sets a document currency and is written against a payables account with its own currency.
    # These two currencies can be different from the company's currency.
    # Outstanding amount is always in the currency of the payables account.
    #
    # If the payables account currency is different from the company account, 
    # ERPNext forces the document currency to match the account currency.
    #
    # In practice: 
    # Company in CHF, supplier in EUR -> invoice always in EUR
    # Company in CHF, supplier in CHF -> invoice in CHF, EUR, USD...
    #
    # There is no "grand total in receivables currency" field. 
    # It's either base_grand_total (company currency) or grand_total (document currency).
    #
    # Consequence: there is no clear outstanding balance in the document currency.

    additional_filters = ""

    if filters.company:
        additional_filters += " AND pi.company = '{company}'".format(company=filters.company)

    query = """
        SELECT 
            pi.posting_date, 
            pi.due_date, 
            DATEDIFF(pi.due_date, pi.posting_date) as payment_terms,
            DATEDIFF(pi.due_date, '{status_date}') as days_till_due,
            pi.supplier as supplier,
            p.supplier_name,
            pi.name as voucher,

            pi.grand_total, 
            pi.currency as document_currency,

            pi.credit_to as payables_account,
            pi.party_account_currency as payables_currency,
            pi.outstanding_amount,

            pi.base_grand_total,
            pi.company
        FROM 
            `tabPurchase Invoice` pi
        JOIN 
            `tabSupplier` p ON p.name = pi.supplier
        WHERE 
            pi.docstatus = 1
            AND pi.outstanding_amount > 0
            {filters}
        ORDER BY days_till_due ASC
    """.format(status_date=filters.status_date, filters=additional_filters)
    data = frappe.db.sql(query, as_dict=True)
    return data