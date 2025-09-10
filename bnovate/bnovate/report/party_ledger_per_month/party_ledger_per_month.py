# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    from_date = frappe.utils.getdate(filters.get("from_date"))
    to_date = frappe.utils.getdate(filters.get("to_date"))
    months = []
    while from_date <= to_date:
        months.append(f"{from_date.year}-{from_date.month:02d}")
        from_date = frappe.utils.add_months(from_date, 1)

    columns = [
        {"label": "Expense Account", "fieldname": "expense_account", "fieldtype": "Link", "options": "Account", "width": 150},
        {"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 150},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 150},
        {"label": "Supplier Name", "fieldname": "supplier_name", "fieldtype": "Data", "width": 150},
        {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150}
    ]

    for month in months:
        columns.append({"label": month, "fieldname": month, "fieldtype": "Currency", "width": 120})

    return columns

def get_columns_old():
    columns = [
        {"label": "Year", "fieldname": "year", "fieldtype": "Int", "width": 80},
        {"label": "Month", "fieldname": "month", "fieldtype": "Int", "width": 80},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": "Invoice Name", "fieldname": "name", "fieldtype": "Data", "width": 150},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 150},
        {"label": "Supplier Name", "fieldname": "supplier_name", "fieldtype": "Data", "width": 150},
        {"label": "Expense Account", "fieldname": "expense_account", "fieldtype": "Link", "options": "Account", "width": 150},
        {"label": "Sum Net Amount", "fieldname": "base_net_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150}
    ]
    return columns

def get_data(filters):

    sql = """
        SELECT 
            YEAR(pi.posting_date) as year,
            MONTH(pi.posting_date) as month,
            pi.posting_date,
            pi.name,
            pi.supplier,
            s.supplier_name,
            pii.expense_account,
            pii.cost_center,
            SUM(pii.base_net_amount) as base_net_amount,
            pi.company
        FROM `tabPurchase Invoice Item` pii
        JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        JOIN `tabSupplier` s ON s.name = pi.supplier
        WHERE pi.posting_date BETWEEN "{from_date}" AND "{to_date}"
        GROUP BY 
            YEAR(pi.posting_date),
            MONTH(pi.posting_date),
            pii.cost_center,
            pi.supplier,
            pii.expense_account
        ORDER BY pii.expense_account, pi.supplier
    """.format(from_date=filters.get("from_date"), to_date=filters.get("to_date"))

    data = frappe.db.sql(sql, as_dict=True)

    # Create a dictionary to hold the pivoted data
    pivot_data = {}
    for row in data:
        key = (row['expense_account'], row['supplier'], row['cost_center'])
        if key not in pivot_data:
            pivot_data[key] = {'expense_account': row['expense_account'], 'cost_center': row['cost_center'], 'supplier': row['supplier'], 'supplier_name': row['supplier_name'], 'company': row['company']}
        pivot_data[key][f"{row['year']}-{row['month']:02d}"] = row['base_net_amount']

    # Convert the dictionary to a list of dictionaries
    pivoted_data = []
    for key, value in pivot_data.items():
        pivoted_data.append(value)

    # Get all the months in the interval
    from_date = frappe.utils.getdate(filters.get("from_date"))
    to_date = frappe.utils.getdate(filters.get("to_date"))
    months = []
    while from_date <= to_date:
        months.append(f"{from_date.year}-{from_date.month:02d}")
        from_date = frappe.utils.add_months(from_date, 1)

    # Add missing months with zero values
    for row in pivoted_data:
        for month in months:
            if month not in row:
                row[month] = 0

    return pivoted_data

