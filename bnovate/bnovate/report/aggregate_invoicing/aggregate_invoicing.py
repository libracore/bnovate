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
import re
import frappe
import calendar
import datetime

from frappe import _
from frappe.utils import cint, today
from email.policy import default

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


def get_columns(filters):
    cols = [
        {'fieldname': 'customer', 'label': _('Customer'), 'fieldtype': 'Link', 'options': 'Customer', 'width': 100},
        {'fieldname': 'customer_name', 'label': _('Customer name'), 'fieldtype': 'Data', 'width': 150},
        {'fieldname': 'reference', 'label': _('Reference'), 'fieldtype': 'Dynamic Link', 'options': 'dt', 'width': 100},
        {'fieldname': 'date', 'label': _('Start Billing / Ship Date'), 'fieldtype': 'Date', 'width': 80},
        {'fieldname': 'period_end', 'label': _('End Billing Period'), 'fieldtype': 'Date', 'width': 80},
        {'fieldname': 'item_code', 'label': _('Item'), 'fieldtype': 'Link', 'options': 'Item', 'width': 200, 'align': 'left'},
        {'fieldname': 'qty', 'label': _('Qty'), 'fieldtype': 'Float', 'width': 50},
        {'fieldname': 'rate', 'label': _('Item Rate'), 'fieldtype': 'Currency', 'options': 'currency', 'width': 100},
        {'fieldname': 'amount', 'label': _('Total'), 'fieldtype': 'Currency', 'options': 'currency', 'width': 100},
        {'fieldname': 'shipping', 'label': _('Shipping'), 'fieldtype': 'Currency', 'options': 'currency', 'width': 100},
        {'fieldname': 'payment_terms_template', 'label': _('Payment Terms'), 'fieldtype': 'link', 'options': 'Payment Terms Template', 'width': 120},
        {'fieldname': 'action', 'label': _('Action'), 'fieldtype': 'Data', 'width': 170},
        {'fieldname': 'sub_interval', 'label': _('Interval'), 'fieldtype': 'Data', 'width': 80},
        {'fieldname': 'start_date', 'label': _('Start Subscription'), 'fieldtype': 'Date', 'width': 80},
        {'fieldname': 'end_date', 'label': _('End Subscription'), 'fieldtype': 'Date', 'width': 80},
    ]

    if filters.show_invoiced:
        cols.extend([
            {'fieldname': 'sinv_name', 'label': _('Invoice'), 'fieldtype': 'Link', 'options': 'Sales Invoice', 'width': 100},
            {'fieldname': 'posting_date', 'label': _('Posting Date'), 'fieldtype': 'Date', 'width': 80},
            {'fieldname': 'sii_start_date', 'label': _('SINV Start Period'), 'fieldtype': 'Date', 'width': 80},
            {'fieldname': 'sii_end_date', 'label': _('SINV End Period'), 'fieldtype': 'Date', 'width': 80},
        ])

    return cols

def get_data(filters):
    entries = get_invoiceable_entries(from_date=filters.from_date, 
        to_date=filters.to_date, customer=filters.customer,
        show_invoiced=filters.show_invoiced,
        doctype=filters.doctype,
        ignore_stopped=filters.ignore_stopped)

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
                if e.payment_terms_template: payment_terms.add(e.payment_terms_template)
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


def get_invoiceable_entries(from_date=None, to_date=None, customer=None, doctype=None, 
    subscription=None, show_invoiced=False, show_drafts=True, ignore_stopped=True):
    if not from_date:
        from_date = "2000-01-01"
    if not to_date:
        to_date = today()
    if not customer:
        customer = "%"
    sinv_docstatus = "= 1"
    if show_drafts:
        sinv_docstatus = "< 2"

    if subscription:
        # Don't show DN
        doctype = "Subscription Contract"
    else:
        subscription = "%"

    invoiced_filter = ""
    if show_invoiced:
        invoiced_filter = "OR si.docstatus < 2"
    shipping_account = frappe.get_single("bNovate Settings").shipping_income_account

    stopped_filter = ""
    if ignore_stopped:
        stopped_filter = "AND ss.stopped != 1"
        
    sql_query = """
        -- --sql
        SELECT
            1 AS indent,
            dn.customer AS customer,
            dn.customer_name AS customer_name,
            dn.posting_date AS date,
            "Delivery Note" AS dt,
            dn.name AS reference,
            dni.against_sales_order AS sales_order,
            dni.so_detail AS so_detail,
            dni.name AS detail,
            dni.item_code,
            dni.item_name AS item_name,
            NULL AS hours,
            dni.qty AS qty,
            dni.net_rate AS rate,
            dni.price_list_rate AS price_list_rate,
            dni.amount AS amount,
            dn.discount_amount AS additional_discount,
            dn.currency AS currency,
            dni.description,
            dn.po_no,
            dni.blanket_order_customer_reference,
            IFNULL(dns.shipping, 0) AS shipping,
            dn.payment_terms_template,
            dn.taxes_and_charges,
            dn.incoterm,

            -- Only relevant for subscriptions:
            NULL AS sub_interval,
            NULL AS start_date,
            NULL AS end_date,
            NULL AS period_start,
            NULL AS period_end,
            NULL AS sinv_status,
            NULL AS sinv_name,
            NULL AS posting_date,
            NULL AS sii_start_date,
            NULL AS sii_end_date,
            NULL AS ssi_name
        FROM `tabDelivery Note Item` dni
        LEFT JOIN `tabDelivery Note` dn ON dn.name = dni.parent
        LEFT JOIN `tabSales Invoice Item` sii ON (
            dni.name = sii.dn_detail
            AND sii.docstatus {sinv_docstatus}
        )
        LEFT JOIN (
          SELECT
          	stc.parent,
          	stc.tax_amount as shipping
          FROM `tabSales Taxes and Charges` stc
          WHERE stc.account_head = "{shipping_account}"
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
            
        UNION
        -- For each subscription, generate a row for each period between start end end date.
        SELECT * FROM (WITH RECURSIVE bp AS ( -- bp: billing periods
            SELECT
                ss.name,
                ssi.name AS ssi_docname,
                ssi.idx AS ssi_index,
                start_date,
                -- Continue at most until end of current month / filter end date month. For yearly we still generate an invoice for entire year 
                LEAST(IFNULL(ss.end_date, '2099-12-31'), '{to_date}') AS end_date,
                ss.interval,
                start_date as period_start,
                CASE ss.interval
                    WHEN 'Yearly' THEN DATE_ADD(DATE_ADD(start_date, INTERVAL 1 YEAR), INTERVAL -1 DAY)
                    WHEN 'Monthly' THEN DATE_ADD(DATE_ADD(start_date, INTERVAL 1 MONTH), INTERVAL -1 DAY)
                END AS period_end
            FROM `tabSubscription Contract Item` ssi
            JOIN `tabSubscription Contract` ss on ssi.parent = ss.name
            UNION ALL
            SELECT
                name,
                ssi_docname,
                ssi_index,
                start_date,
                end_date,
                bp.interval,
                CASE bp.interval
                    WHEN 'Yearly' THEN DATE_ADD(period_start, INTERVAL 1 YEAR) 
                    WHEN 'Monthly' THEN DATE_ADD(period_start, INTERVAL 1 MONTH)
                END AS period_start,
                CASE bp.interval
                    -- period_start is previous iteration -> add two intervals
                    WHEN 'Yearly' THEN DATE_ADD(DATE_ADD(period_start, INTERVAL 2 YEAR), INTERVAL -1 DAY)
                    WHEN 'Monthly' THEN DATE_ADD(DATE_ADD(period_start, INTERVAL 2 MONTH), INTERVAL -1 DAY)
                END AS period_end
            FROM bp
            WHERE period_end < end_date -- note this is period_end from previous iteration!
        )
        SELECT
            1 AS indent,
            ss.customer AS customer,
            ss.customer_name AS customer_name,
            bp.period_start AS date,
            "Subscription Contract" AS dt,
            ss.name AS reference,
            ssi.name AS detail,
            NULL AS sales_order,
            NULL AS so_detail,
            ssi.item_code,
            ssi.item_name,
            NULL AS hours,
            ssi.qty AS qty,
            ssi.rate AS rate,
            ssi.price_list_rate AS price_list_rate,
            (IFNULL(ssi.qty, 1) * IFNULL(ssi.rate, 0)) AS amount,
            0 as additional_discount,
            ss.currency AS currency,
            ssi.description,
            ss.po_no,
            NULL as blanket_order_customer_reference,
            NULL AS shipping,
            ss.payment_terms_template,
            ss.taxes_and_charges,
            NULL AS incoterm,

            ss.interval AS sub_interval,
            ss.start_date,
            ss.end_date,
            bp.period_start,
            bp.period_end,
            si.status AS sinv_status,
            si.name AS sinv_name,
            si.posting_date,
            sii.service_start_date AS sii_start_date,
            sii.service_end_date AS sii_end_date,
            ssi.name AS ssi_name
        FROM bp
        JOIN `tabSubscription Contract` ss on ss.name = bp.name
        JOIN `tabSubscription Contract Item` ssi on ssi.name = ssi_docname
        LEFT JOIN `tabSales Invoice Item` sii on (
            sii.sc_detail = ssi.name 
            AND sii.service_start_date = bp.period_start
            AND sii.docstatus {sinv_docstatus}
        )
        LEFT JOIN `tabSales Invoice` si on sii.parent = si.name
        WHERE (si.name IS NULL {invoiced_filter})
            AND ss.customer LIKE "{customer}"
            AND (bp.period_start >= "{from_date}" OR "{from_date}" <= bp.period_end) -- Keep contracts active on from_date. end_date already filtered by RECURSIVE above
            AND ss.docstatus = 1
            AND ss.name LIKE "{subscription}"
            {stopped_filter}
        ORDER BY ss.name, period_start, ssi_index
        ) AS subs
        
        ORDER BY reference, date;
    """.format(from_date=from_date, to_date=to_date, customer=customer, shipping_account=shipping_account,
        invoiced_filter=invoiced_filter, subscription=subscription, sinv_docstatus=sinv_docstatus, stopped_filter=stopped_filter)
    entries = frappe.db.sql(sql_query, as_dict=True)

    # Just filter in python...
    if doctype:
        return [e for e in entries if e.dt == doctype]
    return entries

@frappe.whitelist()
def check_invoice_status(docname, end_date):
    """ Return list of invoiceable periods for a subscription.

    Empty list if invoices are up to date.
    """
    # Elementary SQL injection prevention...
    if not re.match(r'^SC-\d{5}(-\d+)?$', docname):
        frappe.throw("Invalid docname for Subscription Contract: {}".format(docname))

    return get_invoiceable_entries(to_date=end_date, subscription=docname, show_drafts=False)


@frappe.whitelist()
def create_invoice(from_date, to_date, customer, doctype):
    # fetch entries
    entries = get_invoiceable_entries(from_date=from_date, to_date=to_date, customer=customer, doctype=doctype)

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

    # Set incoterm, only if they are identical on all DNs.
    incoterms = set(e.incoterm for e in entries if e.incoterm)
    incoterm = None
    if len(incoterms) == 1:
        incoterm = incoterms.pop()
    if len(incoterms) > 1:
        frappe.msgprint(
             _("Multiple incoterms found. Please set them manually or consider invoicing separately."), 
             _("Incoterm Conflict")
        )


    discounts = sum(e.additional_discount for e in entries)
    if discounts:
        frappe.throw("A DN contains an additional discount. I can't handle this. Please create invoice by hand.")

    tax_templates = set(e.taxes_and_charges for e in entries)
    if len(tax_templates) > 1:
        frappe.msgprint(
             _("Multiple taxes and charges templates found, using the default template for this customer. Consider creating the invoice by hand."), 
             _("Tax Conflict")
        )

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
    else:
        default_taxes = tax_templates.pop()

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
        'incoterm': incoterm,
    })

    shipping_total = 0
    shipping_remarks = []
    last_dn = None
    for e in entries:
        item = {
            'item_code': e.item_code,
            'qty': e.qty,
            'rate': e.rate,
            'description': e.description,
            'price_list_rate': e.price_list_rate,
        }
        if e.rate == 0:
            item['discount_percentage'] = 100
        if e.dt == "Delivery Note":
            item['delivery_note'] = e.reference
            item['dn_detail'] = e.detail
            # item['price_list_rate'] = e.price_list_rate
            if e.so_detail:
                item['sales_order'] = e.sales_order
                item['so_detail'] = e.so_detail
            if e.blanket_order_customer_reference:
                item['blanket_order_customer_reference'] = e.blanket_order_customer_reference
            if e.reference != last_dn:
                shipping_total += e.shipping
                shipping_remarks.append("{}: {} {}".format(e.reference, currency, e.shipping))
            last_dn = e.reference
        elif e.dt == "Subscription Contract":
            item['subscription'] = e.reference
            item['sc_detail'] = e.ssi_name
            item['enable_deferred_revenue'] = 1  # Should be automatic if activated on item
            item['service_start_date'] = e.period_start
            item['service_end_date'] = e.period_end

        sinv.append('items', item)

    if shipping_total > 0:
        sinv.append('items', {
            'item_code': shipping_item_code,
            'qty': 1,
            'rate': shipping_total,
            'price_list_rate': shipping_total,
            'description': "Aggregated shipping cost<br>" + "<br>".join(shipping_remarks),
        })
    
    sinv.insert()
    sinv.db_set("po_no", ", ".join(set([e.po_no for e in entries if e.po_no])))
    frappe.db.commit()
    
    return sinv.name