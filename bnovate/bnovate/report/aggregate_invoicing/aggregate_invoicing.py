# Copyright (c) 2023, bNovate, libracore and contributors
# For license information, please see license.txt
#
#
# Create a list of subscriptions and DN items ready to be billed
# - Create a single invoice per customer for all open positions
# - Aggregates shipping cost of all DNs under an item
# - Elementary handling of different currencies and taxes and charges
#

from __future__ import unicode_literals
from email.policy import default
import frappe
from frappe import _
import calendar
import datetime
from frappe.utils import cint

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {'fieldname': 'customer', 'label': _('Customer'), 'fieldtype': 'Link', 'options': 'Customer', 'width': 100},
        {'fieldname': 'customer_name', 'label': _('Customer name'), 'fieldtype': 'Data', 'width': 150},
        {'fieldname': 'date', 'label': _('Date'), 'fieldtype': 'Date', 'width': 80},
        {'fieldname': 'item', 'label': _('Item'), 'fieldtype': 'Link', 'options': 'Item', 'width': 200},
        {'fieldname': 'qty', 'label': _('Qty'), 'fieldtype': 'Float', 'width': 50},
        {'fieldname': 'rate', 'label': _('Item Rate'), 'fieldtype': 'Currency', 'options': 'currency', 'width': 100},
        {'fieldname': 'amount', 'label': _('Total'), 'fieldtype': 'Currency', 'options': 'currency', 'width': 100},
        {'fieldname': 'shipping', 'label': _('Shipping'), 'fieldtype': 'Currency', 'options': 'currency', 'width': 100},
        {'fieldname': 'reference', 'label': _('Reference'), 'fieldtype': 'Dynamic Link', 'options': 'dt', 'width': 120},
        {'fieldname': 'payment_terms_template', 'label': _('Payment Terms'), 'fieldtype': 'link', 'options': 'Payment Terms Template', 'width': 120},
        {'fieldname': 'action', 'label': _('Action'), 'fieldtype': 'Data', 'width': 200}
    ]

def get_data(filters):
    entries = get_invoiceable_entries(from_date=filters.from_date, 
        to_date=filters.to_date, customer=filters.customer)
    
    # find customers
    customers = []
    for e in entries:
        if e.customer not in customers:
            customers.append(e.customer)
    customers.sort()
    
    # create grouped entries
    output = []
    for c in customers:
        details = []
        total_h = 0
        total_amount = 0
        total_shipping = 0
        customer_name = None
        last_dn = None
        currencies = set()
        payment_terms = set()
        for e in entries:
            if e.customer == c:
                total_h += e.hours or 0
                total_amount += ((e.qty or 1) * (e.rate or 0))
                if e.reference != last_dn:  # works if data is sorted by reference
                    total_shipping += e.shipping if e.shipping else 0
                customer_name = e.customer_name
                last_dn = e.reference
                currencies.add(e.currency)
                if e.payment_terms: payment_terms.add(e.payment_terms_template)
                e.customer = None  # Lighten output
                e.customer_name = None
                details.append(e)
                if e.additional_discount:
                    e.action = """<span class="text-warning"><i class="fa fa-warning"></i></span> Additional Discount""" 
                
        # insert customer row
        button = """<button class="btn btn-xs btn-primary" onclick="create_invoice('{customer}')">Create Invoice</button>"""
        warning = ""
        if len(currencies) > 1:
            warning = """<span class="text-warning"><i class="fa fa-warning"></i></span> Multiple currencies"""
        elif len(payment_terms) > 1:
            warning = """<span class="text-warning"><i class="fa fa-warning"></i></span> Multiple payment terms"""
        output.append({
            'dt': 'Customer',
            'customer': c,
            'customer_name': customer_name,
            'hours': total_h,
            'amount': total_amount if len(currencies) == 1 else None,
            'shipping': total_shipping if len(currencies) == 1 else None,
            'action': warning if warning else button.format(customer=c),
            'currency': currencies.pop() if len(currencies) == 1 else None,
            'indent': 0,
        })
        for d in details:
            output.append(d)
            
    return output


def get_invoiceable_entries(from_date=None, to_date=None, customer=None):
    if not from_date:
        from_date = "2000-01-01"
    if not to_date:
        to_date = "2099-12-31"
    if not customer:
        customer = "%"
        
    sql_query = """
        SELECT
            dn.customer AS customer,
            dn.customer_name AS customer_name,
            dn.posting_date AS date,
            "Delivery Note" AS dt,
            dn.name AS reference,
            dni.against_sales_order AS sales_order,
            dni.so_detail AS so_detail,
            dni.name AS detail,
            dni.item_code AS item,
            dni.item_name AS item_name,
            NULL AS hours,
            dni.qty AS qty,
            dni.net_rate AS rate,
            dni.price_list_rate AS price_list_rate,
            dni.amount AS amount,
            dn.discount_amount AS additional_discount,
            dn.currency AS currency,
            dni.description AS remarks,
            "" AS additional_remarks,
            dni.blanket_order_customer_reference,
            IFNULL(dns.shipping, 0) AS shipping,
            dn.payment_terms_template,
            1 AS indent
        FROM `tabDelivery Note Item` dni
        LEFT JOIN `tabDelivery Note` dn ON dn.name = dni.parent
        LEFT JOIN `tabSales Invoice Item` sii ON (
            dni.name = sii.dn_detail
            AND sii.docstatus < 2
        )
        LEFT JOIN (
          SELECT
          	stc.parent,
          	stc.tax_amount as shipping
          FROM `tabSales Taxes and Charges` stc
          WHERE stc.account_head = "3410 - Freight Out Sales - bN"
        ) as dns ON dns.parent = dn.name # DNS = Delivery Note Shipping
        WHERE 
            dn.docstatus = 1
            AND dn.status != "Closed"
            AND dn.status != "Completed"
            AND !dn.is_return
            AND dn.grand_total > 0
            AND dn.customer LIKE "{customer}"
            AND (dn.posting_date >= "{from_date}" AND dn.posting_date <= "{to_date}")
            AND sii.name IS NULL
            
        UNION SELECT
            ss.customer AS customer,
            ss.customer_name AS customer_name,
            ss.start_date AS date,
            "Subscription Service" AS dt,
            ss.name AS reference,
            ssi.name AS detail,
            NULL AS sales_order,
            NULL AS so_detail,
            ssi.item AS item,
            ssi.item_name AS item_name,
            NULL AS hours,
            ssi.qty AS qty,
            ssi.rate AS rate,
            NULL AS price_list_rate,
            (IFNULL(ssi.qty, 1) * IFNULL(ssi.rate, 0)) AS amount,
            0 as additional_discount,
            "CHF" AS currency,
            ss.name AS remarks,
            NULL as blanket_order_customer_reference,
            IFNULL(ss.remarks, "") AS additional_remarks,
            NULL AS shipping,
            ss.payment_terms_template,
            1 AS indent
        FROM `tabSubscription Service Item` ssi
        LEFT JOIN `tabSubscription Service` ss ON ss.name = ssi.parent
        WHERE
            ss.enabled = 1
            AND ss.customer LIKE "{customer}"
            AND ss.start_date <= "{to_date}" 
            AND (ss.end_date IS NULL OR ss.end_date >= "{to_date}")
            AND ((ss.interval = "Monthly" AND (SELECT IFNULL(MAX(tAI1.date), "2000-01-01") 
                                                      FROM `tabSubscription Service Invoice` AS tAI1
                                                      WHERE tAI1.parent = ss.name) <= DATE_FORMAT(NOW() ,'%Y-%m-01'))
                 OR (ss.interval = "Yearly" AND (SELECT IFNULL(MAX(tAI2.date), "2000-01-01")
                                                      FROM `tabSubscription Service Invoice` AS tAI2
                                                      WHERE tAI2.parent = ss.name) <= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 12 MONTH) ,'%Y-%m-01'))
                )
        
        ORDER BY date ASC, reference;
    """.format(from_date=from_date, to_date=to_date, customer=customer)
    entries = frappe.db.sql(sql_query, as_dict=True)
    return entries


@frappe.whitelist()
def create_invoice(from_date, to_date, customer):
    # fetch entries
    entries = get_invoiceable_entries(from_date=from_date, to_date=to_date, customer=customer)

    # Refuse to create invoice for mixed currency:
    currencies = set(e.currency for e in entries)
    if len(currencies) > 1:
        frappe.throw("Can't generate invoice for different currencies. Please create them by hand.")
    currency = currencies.pop()

    # Refuse to create invoices for mixed payment terms (ignore empty ones) 
    payment_terms_templates = set(e.payment_terms_template for e in entries if e.payment_terms_template)
    if len(payment_terms_templates) > 1:
        frappe.throw("Can't generate invoice for different payment terms. Please create them by hand.")
    payment_terms = payment_terms_templates.pop() if payment_terms_templates else None

    discounts = sum(e.additional_discount for e in entries)
    if discounts:
        frappe.throw("A DN contains an additional discount. I can't handle this. Please create invoice by hand.")
    
    # determine tax template
    customer_group_name = frappe.get_value("Customer", customer, "customer_group")
    customer_group = frappe.get_doc("Customer Group", customer_group_name)
    default_taxes = customer_group.taxes_and_charges_template
    # default_taxes = frappe.get_all("Sales Taxes and Charges Template", filters={'is_default': 1}, fields=['name'])
    if not default_taxes:
        frappe.throw(
             _("Please define a default sales taxes and charges template for customer group {}.".format(customer_group_name)), 
             _("Configuration missing")
        )
    taxes_and_charges_template = frappe.get_doc("Sales Taxes and Charges Template", default_taxes)

    # Determine shipping item
    shipping_item_code = frappe.get_single("bNovate Settings").shipping_income_item
    
    # create sales invoice
    sinv = frappe.get_doc({
        'doctype': "Sales Invoice",
        'customer': customer,
        'customer_group': frappe.get_value("Customer", customer, "customer_group"),
        'currency': currency,
        'taxes_and_charges': default_taxes,
        'taxes': taxes_and_charges_template.taxes,
        'payment_terms_template': payment_terms,
    })
    
    shipping_total = 0
    shipping_remarks = []
    last_dn = None
    for e in entries:
        #Format Remarks 
        remarkstring = e.remarks.replace("\n", "<br>")
        remarkstring += ("<br>" + e.additional_remarks.replace("\n", "<br>")) if e.additional_remarks else ""

        item = {
            'item_code': e.item,
            'qty': e.qty,
            'rate': e.rate,
            'description': remarkstring,
        }
        if e.dt == "Delivery Note":
            item['delivery_note'] = e.reference
            item['dn_detail'] = e.detail
            item['price_list_rate'] = e.price_list_rate
            if e.so_detail:
                item['sales_order'] = e.sales_order
                item['so_detail'] = e.so_detail
            if e.blanket_order_customer_reference:
                item['blanket_order_customer_reference'] = e.blanket_order_customer_reference
            if e.reference != last_dn:
                shipping_total += e.shipping
                shipping_remarks.append("{}: {} {}".format(e.reference, currency, e.shipping))
            last_dn = e.reference
        elif e.dt == "Subscription Service":
            item['subscription'] = e.reference

        sinv.append('items', item)

    if shipping_total > 0:
        sinv.append('items', {
            'item_code': shipping_item_code,
            'qty': 1,
            'rate': shipping_total,
            'description': "Aggregated shipping cost<br>" + "<br>".join(shipping_remarks),
        })
    
    sinv.insert()
    
    # insert abo references (*renamed Abo to Subscription Service)
    abos = []
    for e in entries:
        if e.dt == "Subscription Service" and e.reference not in abos:
            abos.append(e.reference)
    for a in abos:
        abo = frappe.get_doc("Subscription Service", a)
        abo.append("invoices", {
            'date': datetime.datetime.now(),
            'sales_invoice': sinv.name
        })
        abo.save()
    
    frappe.db.commit()
    
    return sinv.name