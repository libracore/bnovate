# Copyright (c) 2023, bNovate, libracore and contributors
# For license information, please see license.txt

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
        {'fieldname': 'rate', 'label': _('Rate'), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'reference', 'label': _('Reference'), 'fieldtype': 'Dynamic Link', 'options': 'dt', 'width': 120},
        {'fieldname': 'action', 'label': _('Action'), 'fieldtype': 'Data', 'width': 100}
    ]

def get_data(filters):
    entries = get_invoiceable_entries(from_date=filters.from_date, 
        to_date=filters.to_date, customer=filters.customer)
    
    # find customers
    customers = []
    for e in entries:
        if e.customer not in customers:
            customers.append(e.customer)
    
    # create grouped entries
    output = []
    for c in customers:
        details = []
        total_h = 0
        total_amount = 0
        customer_name = None
        for e in entries:
            if e.customer == c:
                total_h += e.hours or 0
                total_amount += ((e.qty or 1) * (e.rate or 0))
                customer_name = e.customer_name
                details.append(e)
                
        # insert customer row
        output.append({
            'customer': c,
            'customer_name': customer_name,
            'hours': total_h,
            'rate': total_amount,
            'action': '''<button class="btn btn-xs btn-primary" onclick="create_invoice('{customer}')">Create Invoice</button>'''.format(customer=c),
            'indent': 0
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
            NULL AS employee_name,
            dni.name AS detail,
            dni.item_code AS item,
            dni.item_name AS item_name,
            NULL AS hours,
            dni.qty AS qty,
            dni.net_rate AS rate,
            dn.name AS remarks,
            "" AS additional_remarks,
            1 AS indent
        FROM `tabDelivery Note Item` dni
        LEFT JOIN `tabDelivery Note` dn ON dn.name = dni.parent
        LEFT JOIN `tabSales Invoice Item` sii ON (
            dni.name = sii.dn_detail
            AND sii.docstatus < 2
        )
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
            NULL AS employee_name,
            ssi.name AS detail,
            ssi.item AS item,
            ssi.item_name AS item_name,
            NULL AS hours,
            ssi.qty AS qty,
            ssi.rate AS rate,
            ss.name AS remarks,
            IFNULL(ss.remarks, "") AS additional_remarks,
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
        
        ORDER BY date ASC;
    """.format(from_date=from_date, to_date=to_date, customer=customer)
    entries = frappe.db.sql(sql_query, as_dict=True)
    return entries


@frappe.whitelist()
def create_invoice(from_date, to_date, customer):
    # fetch entries
    entries = get_invoiceable_entries(from_date=from_date, to_date=to_date, customer=customer)
    
    # determine tax template
    default_taxes = frappe.get_all("Sales Taxes and Charges Template", filters={'is_default': 1}, fields=['name'])
    if len(default_taxes) == 0:
        frappe.throw( _("Please define a default sales taxes and charges template."), _("Configuration missing"))
    taxes_and_charges_template = frappe.get_doc("Sales Taxes and Charges Template", default_taxes[0]['name'])
    
    # create sales invoice
    sinv = frappe.get_doc({
        'doctype': "Sales Invoice",
        'customer': customer,
        'customer_group': frappe.get_value("Customer", customer, "customer_group"),
        'taxes_and_charges': default_taxes[0]['name'],
        'taxes': taxes_and_charges_template.taxes,
    })
    
    for e in entries:
        #Format Remarks 
        if e.remarks:
            remarkstring = "{0} : {1} <br>{2}<br>{3}".format(e.date.strftime("%d.%m.%Y"), 
                e.employee_name or e.item_name, 
                e.remarks.replace("\n", "<br>"),
                e.additional_remarks.replace("\n", "<br>")
                )
        else:
            remarkstring = "{0} : {1}".format(e.date.strftime("%d.%m.%Y"), e.employee_name)

        item = {
            'item_code': e.item,
            'qty': e.qty,
            'rate': e.rate,
            'description': remarkstring,
            'remarks': remarkstring

        }
        if e.dt == "Delivery Note":
            item['delivery_note'] = e.reference
            item['dn_detail'] = e.detail
        elif e.dt == "Timesheet":
            item['timesheet'] = e.reference
            item['ts_detail'] = e.detail
            item['qty'] = e.hours
     
        sinv.append('items', item)
    
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