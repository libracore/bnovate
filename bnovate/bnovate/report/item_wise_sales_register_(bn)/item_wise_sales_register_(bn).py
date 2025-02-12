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
	return _execute(filters)

def _execute(filters=None, additional_table_columns=None, additional_query_columns=None):
	if not filters: filters = {}
	# filters.update({"from_date": filters.get("date_range") and filters.get("date_range")[0], "to_date": filters.get("date_range") and filters.get("date_range")[1]})
	columns = get_columns(additional_table_columns)


	item_list = get_items(filters, additional_query_columns)
	return columns, item_list


	if item_list:
		itemised_tax, tax_columns = get_tax_accounts(item_list, columns, company_currency)
	mode_of_payments = get_mode_of_payments(set([d.parent for d in item_list]))
	so_dn_map = get_delivery_notes_against_sales_order(item_list)

	data = []
	for d in item_list:
		delivery_note = None
		if d.delivery_note:
			delivery_note = d.delivery_note
		elif d.so_detail:
			delivery_note = ", ".join(so_dn_map.get(d.so_detail, []))

		if not delivery_note and d.update_stock:
			delivery_note = d.parent

		d.delivery_note = delivery_note

		row = [d.item_code, d.item_name, d.item_group, d.description, d.parent, d.posting_date, d.customer, d.customer_name]

		if additional_query_columns:
			for col in additional_query_columns:
				row.append(d.get(col))

		d.mode_of_payments = ", ".join(mode_of_payments.get(d.parent, []))
		row += [
			d.customer_group, d.debit_to, ", ".join(mode_of_payments.get(d.parent, [])),
			d.territory, d.project, d.company, d.sales_order,
			delivery_note, d.income_account, d.cost_center, d.stock_qty, d.stock_uom
		]

		if d.stock_uom != d.uom and d.stock_qty:
			d.base_net_rate = (d.base_net_rate * d.qty)/d.stock_qt 
			row += [(d.base_net_rate * d.qty)/d.stock_qty, d.base_net_amount]
		else:
			row += [d.base_net_rate, d.base_net_amount]

		total_tax = 0
		for tax in tax_columns:
			item_tax = itemised_tax.get(d.name, {}).get(tax, {})

			d[tax + ' Rate'] = item_tax.get("tax_rate", 0)
			d[tax + ' Amount'] = item_tax.get("tax_amount", 0)


			row += [item_tax.get("tax_rate", 0), item_tax.get("tax_amount", 0)]
			total_tax += flt(item_tax.get("tax_amount"))

		row += [total_tax, d.base_net_amount + total_tax, company_currency]


		d.total_tax = total_tax
		d.total = d.base_net_amount + total_tax
		d.base_currency = company_currency

		data.append(row)

	return columns, item_list

def get_columns(additional_table_columns):
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
		}
	]

	if additional_table_columns:
		columns += additional_table_columns

	columns += [
		{
			"fieldname": "customer_group",
			"label": _("Customer Group"),
			"fieldtype": "Link",
			"width": 120,
			"options": "Customer Group"
		},
		# {
		# 	"fieldname": "receivable_account",
		# 	"label": _("Receivable Account"),
		# 	"fieldtype": "Link",
		# 	"width": 120,
		# 	"options": "Account"
		# },
		# {
		# 	"fieldname": "mode_of_payment",
		# 	"label": _("Mode of Payment"),
		# 	"fieldtype": "Data",
		# 	"width": 120
		# },
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
			"fieldname": "company_currency",
			"label": _("Company Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"width": 100
		},
		{
			"fieldname": "base_net_rate",
			"label": _("Net Rate"),
			"fieldtype": "Currency",
			"width": 120,
			"options": "company_currency"
		},
		{
			"fieldname": "base_net_amount",
			"label": _("Net Amount"),
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

def get_items(filters, additional_query_columns):
	conditions = get_conditions(filters)
	match_conditions = frappe.build_match_conditions("Sales Invoice")

	if match_conditions:
		match_conditions = " and {0} ".format(match_conditions)

	if additional_query_columns:
		additional_query_columns = ', ' + ', '.join(additional_query_columns)

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
			sii.qty {0}
		FROM `tabSales Invoice` si
		LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		LEFT JOIN `tabCustomer` cu ON cu.name = si.customer
		LEFT JOIN `tabItem` it ON it.item_code = sii.item_code
		LEFT JOIN `tabTerritory` te ON te.name = cu.territory
		LEFT JOIN `tabCompany` co ON co.name = si.company
		WHERE si.docstatus = 1 %s %s
		ORDER BY si.posting_date DESC, sii.item_code DESC
		""".format(additional_query_columns or '', company_currency=company_currency) % (conditions, match_conditions), filters, as_dict=1)

def get_delivery_notes_against_sales_order(item_list):
	so_dn_map = frappe._dict()
	so_item_rows = list(set([d.so_detail for d in item_list]))

	if so_item_rows:
		delivery_notes = frappe.db.sql("""
			select parent, so_detail
			from `tabDelivery Note Item`
			where docstatus=1 and so_detail in (%s)
			group by so_detail, parent
		""" % (', '.join(['%s']*len(so_item_rows))), tuple(so_item_rows), as_dict=1)

		for dn in delivery_notes:
			so_dn_map.setdefault(dn.so_detail, []).append(dn.parent)

	return so_dn_map

def get_deducted_taxes():
	return frappe.db.sql_list("select name from `tabPurchase Taxes and Charges` where add_deduct_tax = 'Deduct'")

def get_tax_accounts(item_list, columns, company_currency,
		doctype="Sales Invoice", tax_doctype="Sales Taxes and Charges"):
	import json
	item_row_map = {}
	tax_columns = []
	invoice_item_row = {}
	itemised_tax = {}

	tax_amount_precision = get_field_precision(frappe.get_meta(tax_doctype).get_field("tax_amount"),
		currency=company_currency) or 2

	for d in item_list:
		invoice_item_row.setdefault(d.parent, []).append(d)
		item_row_map.setdefault(d.parent, {}).setdefault(d.item_code or d.item_name, []).append(d)

	conditions = ""
	if doctype == "Purchase Invoice":
		conditions = " and category in ('Total', 'Valuation and Total') and base_tax_amount_after_discount_amount != 0"

	deducted_tax = get_deducted_taxes()
	tax_details = frappe.db.sql("""
		select
			name, parent, description, item_wise_tax_detail,
			charge_type, base_tax_amount_after_discount_amount
		from `tab%s`
		where
			parenttype = %s and docstatus = 1
			and (description is not null and description != '')
			and parent in (%s)
			%s
		order by description
	""" % (tax_doctype, '%s', ', '.join(['%s']*len(invoice_item_row)), conditions),
		tuple([doctype] + list(invoice_item_row)))

	for name, parent, description, item_wise_tax_detail, charge_type, tax_amount in tax_details:
		description = handle_html(description)
		if description not in tax_columns and tax_amount:
			# as description is text editor earlier and markup can break the column convention in reports
			tax_columns.append(description)

		if item_wise_tax_detail:
			try:
				item_wise_tax_detail = json.loads(item_wise_tax_detail)

				for item_code, tax_data in item_wise_tax_detail.items():
					itemised_tax.setdefault(item_code, frappe._dict())

					if isinstance(tax_data, list):
						tax_rate, tax_amount = tax_data
					else:
						tax_rate = tax_data
						tax_amount = 0

					if charge_type == "Actual" and not tax_rate:
						tax_rate = "NA"

					item_net_amount = sum([flt(d.base_net_amount)
						for d in item_row_map.get(parent, {}).get(item_code, [])])

					for d in item_row_map.get(parent, {}).get(item_code, []):
						item_tax_amount = flt((tax_amount * d.base_net_amount) / item_net_amount) \
							if item_net_amount else 0
						if item_tax_amount:
							tax_value = flt(item_tax_amount, tax_amount_precision)
							tax_value = (tax_value * -1
								if (doctype == 'Purchase Invoice' and name in deducted_tax) else tax_value)

							itemised_tax.setdefault(d.name, {})[description] = frappe._dict({
								"tax_rate": tax_rate,
								"tax_amount": tax_value
							})

			except ValueError:
				continue
		elif charge_type == "Actual" and tax_amount:
			for d in invoice_item_row.get(parent, []):
				itemised_tax.setdefault(d.name, {})[description] = frappe._dict({
					"tax_rate": "NA",
					"tax_amount": flt((tax_amount * d.base_net_amount) / d.base_net_total,
						tax_amount_precision)
				})

	tax_columns.sort()
	for desc in tax_columns:
		columns.append({
			"fieldname": desc + " Rate",
			"label": desc + " Rate",
			"fieldtype": "Data",
			"width": 80,
		})
		columns.append({
			"fieldname": desc + " Amount",
			"label": desc + " Amount",
			"fieldtype": "Currency",
			"width": 100,
			"options": "base_currency"
		})

	columns += [{
			"fieldname": "total_tax",
			"label": "Total Tax",
			"fieldtype": "Currency",
			"width": 80,
			"options": "base_currency",
		}, {
			"fieldname": "total",
			"label": "Total",
			"fieldtype": "Currency",
			"width": 100,
			"options": "base_currency"
		}]

	return itemised_tax, tax_columns
