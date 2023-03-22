# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    cols = [
        {'fieldname': 'customer', 'label': _('Customer'), 'fieldtype': 'Link', 'options': 'Customer', 'width': 100},
        {'fieldname': 'customer_name', 'label': _('Customer name'), 'fieldtype': 'Data', 'width': 150},
        {'fieldname': 'subscription', 'label': _('Subscription'), 'fieldtype': 'Link', 'options': 'Subscription Contract', 'width': 100},
        # {'fieldname': 'item_code', 'label': _('Item'), 'fieldtype': 'Link', 'options': 'Item', 'width': 200, 'align': 'left'},
        # {'fieldname': 'qty', 'label': _('Qty'), 'fieldtype': 'Float', 'width': 50},
        # {'fieldname': 'rate', 'label': _('Item Rate'), 'fieldtype': 'Currency', 'options': 'currency', 'width': 100},
        {'fieldname': 'sub_interval', 'label': _('Interval'), 'fieldtype': 'Data', 'width': 80},
        {'fieldname': 'start_date', 'label': _('Start Date'), 'fieldtype': 'Date', 'width': 80},
        {'fieldname': 'planned_end_date', 'label': _('Planned End Date'), 'fieldtype': 'Date', 'width': 80},
        {'fieldname': 'end_date', 'label': _('Actual End Date'), 'fieldtype': 'Date', 'width': 80},
    ]
    return cols



def get_data(filters):

    customer_filter = "%"
    if filters.customer:
        customer_filter = filters.customer

    sql_query = """
    -- sql
SELECT
  sc.name AS subscription,
  sc.title,
  sc.customer,
  c.customer_name,
  sc.interval AS sub_interval,
  sc.start_date,
  sc.planned_end_date,
  sc.end_date,
  IFNULL(end_date, 
    IFNULL(planned_end_date, 
        IFNULL((SELECT GREATEST(MAX(end_date), MAX(start_date)) FROM `tabSubscription Contract`), 
            CURRENT_DATE()))) AS computed_end_date
FROM `tabSubscription Contract` sc
JOIN `tabCustomer` c ON sc.customer = c.name
    ;
    """.format(customer_filter=customer_filter)

    data = frappe.db.sql(sql_query, as_dict=True)

    return data