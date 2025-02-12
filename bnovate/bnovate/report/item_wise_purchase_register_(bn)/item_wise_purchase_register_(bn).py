# Copyright (c) 2024, bNovate, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.item_wise_sales_register.item_wise_sales_register import get_tax_accounts

def execute(filters=None):
	return _execute(filters)

def _execute(filters=None, additional_table_columns=None, additional_query_columns=None):
	if not filters: filters = {}

	columns = get_columns(additional_table_columns)
	data = get_items(filters, additional_query_columns)

	return columns, data


	item_list = get_items(filters, additional_query_columns)
	aii_account_map = get_aii_accounts()
	if item_list:
		itemised_tax, tax_columns = get_tax_accounts(item_list, columns, company_currency,
			doctype="Purchase Invoice", tax_doctype="Purchase Taxes and Charges")

	columns.append({
		"fieldname": "currency",
		"label": _("Currency"),
		"fieldtype": "Data",
		"width": 80
	})

	po_pr_map = get_purchase_receipts_against_purchase_order(item_list)

	data = []
	for d in item_list:
		if not d.stock_qty:
			continue

		purchase_receipt = None
		if d.purchase_receipt:
			purchase_receipt = d.purchase_receipt
		elif d.po_detail:
			purchase_receipt = ", ".join(po_pr_map.get(d.po_detail, []))

		expense_account = d.expense_account or aii_account_map.get(d.company)
		row = [d.item_code, d.item_name, d.item_group, d.description, d.parent, d.posting_date, d.supplier,
			d.supplier_name]

		if additional_query_columns:
			for col in additional_query_columns:
				row.append(d.get(col))

		row += [
			d.credit_to, d.mode_of_payment, d.project, d.subsidy, d.company, d.purchase_order,
			purchase_receipt, expense_account, d.stock_qty, d.stock_uom, d.base_net_amount / d.stock_qty, d.base_net_amount
		]

		total_tax = 0
		for tax in tax_columns:
			item_tax = itemised_tax.get(d.name, {}).get(tax, {})
			row += [item_tax.get("tax_rate", 0), item_tax.get("tax_amount", 0)]
			total_tax += flt(item_tax.get("tax_amount"))

		row += [total_tax, d.base_net_amount + total_tax, company_currency]

		data.append(row)

	return columns, data


def get_columns(additional_table_columns):
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
		}
	]

	if additional_table_columns:
		columns += additional_table_columns

	columns += [
		{
			"fieldname": "credit_to",
			"label": _("Payable Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 120
		},
		# {
		# 	"fieldname": "mode_of_payment",
		# 	"label": _("Mode of Payment"),
		# 	"fieldtype": "Link",
		# 	"options": "Mode of Payment",
		# 	"width": 80
		# },
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

def get_items(filters, additional_query_columns):
	conditions = get_conditions(filters)
	match_conditions = frappe.build_match_conditions("Purchase Invoice")

	if match_conditions:
		match_conditions = " and {0} ".format(match_conditions)

	if additional_query_columns:
		additional_query_columns = ', ' + ', '.join(additional_query_columns)

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
   			pii.stock_qty,
			pii.stock_uom,
			pi.currency,
			pii.rate,
			pii.amount,
   			pii.base_net_amount,
			pi.supplier_name, 
   			pi.mode_of_payment {0},
			"{company_currency}" as company_currency
		from
			`tabPurchase Invoice` pi, `tabPurchase Invoice Item` pii
		where
			pi.name = pii.parent and
			pi.docstatus = 1 %s %s
		order by
			pi.posting_date desc, pii.item_code desc
	""".format(additional_query_columns, company_currency=company_currency) % (conditions, match_conditions), filters, as_dict=1)

def get_aii_accounts():
	return dict(frappe.db.sql("select name, stock_received_but_not_billed from tabCompany"))

def get_purchase_receipts_against_purchase_order(item_list):
	po_pr_map = frappe._dict()
	po_item_rows = list(set([d.po_detail for d in item_list]))

	if po_item_rows:
		purchase_receipts = frappe.db.sql("""
			select parent, purchase_order_item
			from `tabPurchase Receipt Item`
			where docstatus=1 and purchase_order_item in (%s)
			group by purchase_order_item, parent
		""" % (', '.join(['%s']*len(po_item_rows))), tuple(po_item_rows), as_dict=1)

		for pr in purchase_receipts:
			po_pr_map.setdefault(pr.po_detail, []).append(pr.parent)

	return po_pr_map
