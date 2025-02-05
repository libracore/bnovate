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
            "fieldname": "customer",
            "label": "Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 120
        }, {
            "fieldname": "customer_name",
            "label": "Customer Name",
            "fieldtype": "Data",
            "width": 150
        }, {
            "fieldname": "voucher",
            "label": "Voucher",
            "fieldtype": "Link",
            "options": "Sales Invoice",
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
			"fieldname": "receivables_account",
			"label": "Receivables Account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 150,
		}, {
			"fieldname": "receivables_currency",
			"label": "Receivables Currency",
			"fieldtype": "Data",
			"width": 100
		}, {
            "fieldname": "outstanding_amount",
            "label": "Outstanding Amount (Receivables Currency)",
            "fieldtype": "Currency",
            "options": "receivables_currency",
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

	# Warnings:
	# Pay attention to document currency, currency of the receivables account, and company currency.
	# See notes in Accounts Payable (bN) report, the pattern is the same.

    additional_filters = ""

    if filters.company:
        additional_filters += " AND si.company = '{company}'".format(company=filters.company)

    query = """
        SELECT 
            si.posting_date, 
            si.due_date, 
            DATEDIFF(si.due_date, si.posting_date) as payment_terms,
            DATEDIFF(si.due_date, '{status_date}') as days_till_due,
            si.customer as customer,
            c.customer_name,
            si.name as voucher,

            si.currency as document_currency,
            si.grand_total, 


			si.debit_to as receivables_account,
			si.party_account_currency as receivables_currency,
            si.outstanding_amount,

            si.base_grand_total,
            si.company
        FROM 
            `tabSales Invoice` si
        JOIN 
            `tabCustomer` c ON c.name = si.customer
        WHERE 
            si.docstatus = 1
            AND si.outstanding_amount > 0
            {filters}
		ORDER BY days_till_due ASC
    """.format(status_date=filters.status_date, filters=additional_filters)
    data = frappe.db.sql(query, as_dict=True)
    return data