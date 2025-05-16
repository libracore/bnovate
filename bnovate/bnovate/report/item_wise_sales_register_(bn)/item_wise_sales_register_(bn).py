# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from frappe.utils import flt
from frappe.model.meta import get_field_precision
from frappe.utils.xlsxutils import handle_html
from erpnext.accounts.report.sales_register.sales_register import get_mode_of_payments

def execute(filters=None):
	if not filters: filters = {}
	columns = get_columns()


	item_list = get_items(filters)
	return columns, item_list


def get_columns():
	columns = [
		{
			"fieldname": "item_code",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"width": 120,
			"options": "Item"
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
			"width": 100,
			"options": "Item Group"
		},
		{
			"fieldname": "description",
			"label": "Description",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "invoice",
			"label": _("Invoice"),
			"fieldtype": "Link",
			"width": 120,
			"options": "Sales Invoice"
		},
		{
			"fieldname": "posting_date",
			"label": _("Posting Date"),
			"fieldtype": "Date",
			"width": 80
		},
		{
			"fieldname": "customer",
			"label": _("Customer"),
			"fieldtype": "Link",
			"width": 120,
			"options": "Customer"
		},
		{
			"fieldname": "customer_name",
			"label": _("Customer Name"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "customer_group",
			"label": _("Customer Group"),
			"fieldtype": "Link",
			"width": 120,
			"options": "Customer Group"
		},
		{
			"fieldname": "territory",
			"label": _("Territory"),
			"fieldtype": "Link",
			"width": 80,
			"options": "Territory"
		},
		{
			"fieldname": "territory_parent",
			"label": _("Territory Parent"),
			"fieldtype": "Link",
			"width": 80,
			"options": "Territory"
		},
		{
			"fieldname": "project",
			"label": _("Project"),
			"fieldtype": "Link",
			"width": 80,
			"options": "Project"
		},
		{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Link",
			"width": 100,
			"options": "Company"
		},
		{
			"fieldname": "sales_order",
			"label": _("Sales Order"),
			"fieldtype": "Link",
			"width": 100,
			"options": "Sales Order"
		},
		{
			"fieldname": "delivery_note",
			"label": _("Delivery Note"),
			"fieldtype": "Link",
			"width": 100,
			"options": "Delivery Note"
		},
		{
			"fieldname": "income_account",
			"label": _("Income Account"),
			"fieldtype": "Link",
			"width": 140,
			"options": "Account"
		},
		{
			"fieldname": "cost_center",
			"label": _("Cost Center"),
			"fieldtype": "Link",
			"width": 140,
			"options": "Cost Center"
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
			"fieldname": "net_rate",
			"label": _("Net Rate"),
			"fieldtype": "Currency",
			"width": 120,
			"options": "currency"
		},
		{
			"fieldname": "net_amount",
			"label": _("Net Amount"),
			"fieldtype": "Currency",
			"width": 120,
			"options": "currency"
		},
		{
			"fieldname": "company_currency",
			"label": _("Company Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"width": 100
		},
		{
			"fieldname": "base_net_rate",
			"label": _("Net Rate in Company Currency"),
			"fieldtype": "Currency",
			"width": 120,
			"options": "company_currency"
		},
		{
			"fieldname": "base_net_amount",
			"label": _("Net Amount in Company Currency"),
			"fieldtype": "Currency",
			"width": 120,
			"options": "company_currency"
		},
		{
			"fieldname": "cogs",
			"label": _("COGS"),
			"fieldtype": "Currency",
			"width": 120,
			"options": "company_currency"
		}
	]

	return columns

def get_conditions(filters):
	conditions = ""

	for opts in (("company", " and company=%(company)s"),
		("customer", " and si.customer = %(customer)s"),
		("item_code", " and si.item_code = %(item_code)s"),
		("from_date", " and si.posting_date>=%(from_date)s"),
		("to_date", " and si.posting_date<=%(to_date)s"),
		("company_gstin", " and si.company_gstin = %(company_gstin)s"),
		("invoice_type", " and si.invoice_type = %(invoice_type)s")):
			if filters.get(opts[0]):
				conditions += opts[1]

	if filters.get("mode_of_payment"):
		conditions += """ and exists(select name from `tabSales Invoice Payment`
			where parent=si.name
				and ifnull(`tabSales Invoice Payment`.mode_of_payment, '') = %(mode_of_payment)s)"""

	if filters.get("warehouse"):
		conditions +=  """ and exists(select name from `tabSales Invoice Item`
			 where parent=si.name
			 	and ifnull(`tabSales Invoice Item`.warehouse, '') = %(warehouse)s)"""


	if filters.get("brand"):
		conditions +=  """ and exists(select name from `tabSales Invoice Item`
			 where parent=si.name
			 	and ifnull(`tabSales Invoice Item`.brand, '') = %(brand)s)"""

	if filters.get("item_group"):
		conditions +=  """ and exists(select name from `tabSales Invoice Item`
			 where parent=si.name
			 	and ifnull(`tabSales Invoice Item`.item_group, '') = %(item_group)s)"""


	return conditions

def get_items(filters):
	conditions = get_conditions(filters)
	match_conditions = frappe.build_match_conditions("Sales Invoice")

	if match_conditions:
		match_conditions = " and {0} ".format(match_conditions)

	company_currency = frappe.get_cached_value('Company',  filters.get("company"),  "default_currency")

	return frappe.db.sql("""
		select
			sii.name, 
			sii.parent as invoice,
			si.posting_date, 
			si.debit_to,
			si.project, 
			si.customer, 
			si.remarks,
			si.territory, 
			si.company, 
			si.base_net_total,

			sii.item_code, 
			it.item_name,
			it.item_group, 
			it.description, 

			sii.sales_order,
			sii.delivery_note, 
			sii.income_account,
			sii.cost_center,
			sii.stock_qty,
			sii.stock_uom, 

			si.currency,
			sii.net_rate,
			sii.net_amount,
			"{company_currency}" as company_currency,
			sii.base_net_rate,
			sii.base_net_amount, 

			cu.customer_name,
			cu.customer_group, 
			cu.territory,
			te.parent_territory AS territory_parent,

			sii.so_detail,
			si.update_stock, 
			sii.uom, 
			sii.qty,
			SUM(sle.stock_value_difference) as cogs
		FROM `tabSales Invoice` si
		LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		LEFT JOIN `tabCustomer` cu ON cu.name = si.customer
		LEFT JOIN `tabItem` it ON it.item_code = sii.item_code
		LEFT JOIN `tabTerritory` te ON te.name = cu.territory
		LEFT JOIN `tabCompany` co ON co.name = si.company
		LEFT JOIN `tabStock Ledger Entry` sle ON sle.voucher_detail_no = sii.dn_detail
		WHERE si.docstatus = 1 %s %s
		ORDER BY si.posting_date DESC, sii.item_code DESC
		""".format(company_currency=company_currency) % (conditions, match_conditions), filters, as_dict=1)
