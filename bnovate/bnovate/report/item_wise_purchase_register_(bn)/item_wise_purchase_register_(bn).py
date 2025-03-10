# Copyright (c) 2024, bNovate, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.item_wise_sales_register.item_wise_sales_register import get_tax_accounts

def execute(filters=None):
	if not filters: filters = {}

	columns = get_columns()
	data = get_items(filters)

	return columns, data


def get_columns():
	columns = [
		{
			"fieldname": "item_code",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "item_group",
			"label": _("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 100
		},
		{
			"fieldname": "description",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "invoice",
			"label": _("Invoice"),
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 120
		},
		{
			"fieldname": "posting_date",
			"label": _("Posting Date"),
			"fieldtype": "Date",
			"width": 80
		},
		{
			"fieldname": "supplier",
			"label": _("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 120
		},
		{
			"fieldname": "supplier_name",
			"label": _("Supplier Name"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "credit_to",
			"label": _("Payable Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 120
		},
		{
			"fieldname": "project",
			"label": _("Project"),
			"fieldtype": "Link",
			"options": "Project",
			"width": 80
		},
		{
			"fieldname": "subsidy",
			"label": _("Subsidy"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"width": 100
		},
		{
			"fieldname": "purchase_order",
			"label": _("Purchase Order"),
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 100
		},
		{
			"fieldname": "purchase_receipt",
			"label": _("Purchase Receipt"),
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 100
		},
		{
			"fieldname": "expense_account",
			"label": _("Expense Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 140
		},
		{
			"fieldname": "cost_center",
			"label": _("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 120
		},
		{
			"fieldname": "stock_qty",
			"label": _("Stock Qty"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "stock_uom",
			"label": _("Stock UOM"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "currency",
			"label": _("Doc Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"width": 100
		},
		{
			"fieldname": "rate",
			"label": _("Rate"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "company_currency",
			"label": _("Company Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"width": 100
		},
		{
			"fieldname": "base_net_amount",
			"label": _("Amount in Company Currency"),
			"fieldtype": "Currency",
			"options": "company_currency",
			"width": 120
		},
	]

	return columns

def get_conditions(filters):
	conditions = ""

	for opts in (("company", " and company=%(company)s"),
		("supplier", " and pi.supplier = %(supplier)s"),
		("item_code", " and pii.item_code = %(item_code)s"),
		("from_date", " and pi.posting_date>=%(from_date)s"),
		("to_date", " and pi.posting_date<=%(to_date)s"),
		("mode_of_payment", " and ifnull(mode_of_payment, '') = %(mode_of_payment)s")):
			if filters.get(opts[0]):
				conditions += opts[1]

	return conditions

def get_items(filters):
	conditions = get_conditions(filters)
	match_conditions = frappe.build_match_conditions("Purchase Invoice")

	if match_conditions:
		match_conditions = " and {0} ".format(match_conditions)

	company_currency = erpnext.get_company_currency(filters.company)

	return frappe.db.sql("""
		select
			pii.name, 
   			pii.parent as invoice, 
      		pi.posting_date,
        	pi.credit_to,
         	pi.company,
			pi.supplier, 
  			pi.remarks,
     		pi.base_net_total,
       		pii.item_code,
			pii.item_name,
   			pii.item_group,
      		pii.description,
			pii.project,
			pi.subsidy,
   			pii.purchase_order,
			pii.purchase_receipt,
   			pii.po_detail,
			pii.expense_account,
			pii.cost_center,
   			pii.stock_qty,
			pii.stock_uom,
			pi.currency,
			pii.rate,
			pii.amount,
   			pii.base_net_amount,
			pi.supplier_name, 
   			pi.mode_of_payment,
			"{company_currency}" as company_currency
		from
			`tabPurchase Invoice` pi, `tabPurchase Invoice Item` pii
		where
			pi.name = pii.parent and
			pi.docstatus = 1 %s %s
		order by
			pi.posting_date desc, pii.item_code desc
	""".format(company_currency=company_currency) % (conditions, match_conditions), filters, as_dict=1)